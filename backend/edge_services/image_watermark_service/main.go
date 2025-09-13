package main

import (
	"bytes"
	_ "embed"
	"encoding/base64"
	"errors"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/jpeg"
	"image/png"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/disintegration/imaging"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	exiflib "github.com/rwcarlsen/goexif/exif"
	"golang.org/x/image/font"
	"golang.org/x/image/font/opentype"
	"golang.org/x/image/math/fixed"
	_ "golang.org/x/image/webp"
)

type WebhookPayload struct {
	ImageBase64              string   `json:"image_base64"`
	ImageURL                 string   `json:"image_url"`
	PhotoType                string   `json:"photo_type"`
	UploadedBy               string   `json:"uploaded_by"`
	PhotoTakenAt             string   `json:"photo_taken_at"`
	AddWatermark             bool     `json:"add_watermark"`
	WatermarkHasCompanyLogo  bool     `json:"watermark_has_company_logo"`
	WatermarkHasSoftwareLogo bool     `json:"watermark_has_software_logo"`
	GPSLatitude              *float64 `json:"gps_latitude"`
	GPSLongitude             *float64 `json:"gps_longitude"`
	DeviceInfo               string   `json:"device_info"`
	CompanyLogoURL           string   `json:"company_logo_url"`
}

//go:embed assets/solidfield_logo_gray.png
var softwareLogoBytes []byte

//go:embed assets/Inter.ttf
var fontBytes []byte

// I dont need this
func envOr(key, def string) string {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	return v
}

func must(err error) {
	if err != nil {
		log.Fatal(err)
	}
}

func textWidthPx(face font.Face, s string) int {
	d := &font.Drawer{Face: face}
	return int(d.MeasureString(s) >> 6) // converte 26.6 fix -> px
}

func cloneToNRGBA(src image.Image) *image.NRGBA {
	b := src.Bounds()
	dst := image.NewNRGBA(image.Rect(0, 0, b.Dx(), b.Dy()))
	// usa draw para copiar para memória 100% gerenciada pelo Go
	draw.Draw(dst, dst.Bounds(), src, b.Min, draw.Src)
	return dst
}

func wrapLines(face font.Face, text string, maxWidth int) []string {
	words := strings.Fields(text)
	if len(words) == 0 {
		return []string{""}
	}

	var lines []string
	cur := words[0]
	for _, w := range words[1:] {
		test := cur + " " + w
		if textWidthPx(face, test) <= maxWidth {
			cur = test
		} else {
			lines = append(lines, cur)
			cur = w
		}
	}
	lines = append(lines, cur)
	return lines
}

func decodeImageWithEXIF(b []byte) (image.Image, string, error) {
	// PNG “puro”
	if img, err := png.Decode(bytes.NewReader(b)); err == nil {
		return img, "png", nil
	}
	// JPEG (com correção de orientação se você já tinha isso)
	if img, err := jpeg.Decode(bytes.NewReader(b)); err == nil {
		img = normalizeOrientationJPEG(b, img, "jpeg")
		return img, "jpeg", nil
	}

	// === HEIC/AVIF: converte para JPEG antes de seguir ===
	switch sniffFormat(b) {
	case "heic", "avif":
		// converte (tenta interno; se falhar, usa heif-convert)
		jb, err := heifToJPEGBytes(b, 90)
		if err != nil {
			return nil, "", fmt.Errorf("heif/avif convert->jpeg failed: %w", err)
		}
		img, err := jpeg.Decode(bytes.NewReader(jb))
		if err != nil {
			return nil, "", fmt.Errorf("jpeg decode after heif convert failed: %w", err)
		}
		// já vem rasterizado na orientação correta pelo decoder HEIF
		return img, "jpeg", nil
	}

	// Genérico (WEBP incluso via import em branco)
	img, format, err := image.Decode(bytes.NewReader(b))
	if err != nil {
		return nil, "", err
	}
	if format == "jpeg" || format == "jpg" {
		img = normalizeOrientationJPEG(b, img, format)
	}
	return img, format, nil
}

func sniffFormat(b []byte) string {
	if len(b) >= 12 && string(b[4:8]) == "ftyp" {
		brand := string(b[8:12])
		switch brand {
		case "heic", "heix", "heis", "heim", "hevc", "hevx", "mif1", "msf1":
			return "heic" // trata como HEIF/HEIC (HEVC)
		case "avif", "avis":
			return "avif" // HEIF com AV1 (AVIF)
		}
	}
	if len(b) >= 12 && string(b[:4]) == "RIFF" && string(b[8:12]) == "WEBP" {
		return "webp"
	}
	if len(b) >= 8 && bytes.Equal(b[:8], []byte{0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n'}) {
		return "png"
	}
	if len(b) >= 2 && b[0] == 0xFF && b[1] == 0xD8 {
		return "jpeg"
	}
	return ""
}

func loadImageFromURL(url string) (image.Image, string, error) {
	client := &http.Client{Timeout: 15 * time.Second}
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, "", err
	}
	req.Header.Set("User-Agent", "CoreSF-ImageWatermarker/1.0")
	req.Header.Set("Referer", url)

	resp, err := client.Do(req)
	if err != nil {
		return nil, "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode > 299 {
		return nil, "", fmt.Errorf("fetch failed: status %d", resp.StatusCode)
	}
	b, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, "", err
	}
	return decodeImageWithEXIF(b)
}

func loadImageFromBase64(s string) (image.Image, string, error) {
	s = strings.TrimSpace(s)
	data, err := base64.StdEncoding.DecodeString(s)
	if err != nil {
		return nil, "", err
	}
	return decodeImageWithEXIF(data)
}

func loadPNGFromPath(path string) (image.Image, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	img, err := png.Decode(f)
	if err != nil {
		return nil, err
	}
	return img, nil
}

func loadImageFromURLIfPresent(url string) (image.Image, error) {
	if strings.TrimSpace(url) == "" {
		return nil, nil
	}
	img, _, err := loadImageFromURL(url)
	return img, err
}

func drawBorder(dst draw.Image, thickness int, c color.Color) {
	b := dst.Bounds()
	// Top
	draw.Draw(dst, image.Rect(b.Min.X, b.Min.Y, b.Max.X, b.Min.Y+thickness), &image.Uniform{C: c}, image.Point{}, draw.Src)
	// Bottom
	draw.Draw(dst, image.Rect(b.Min.X, b.Max.Y-thickness, b.Max.X, b.Max.Y), &image.Uniform{C: c}, image.Point{}, draw.Src)
	// Left
	draw.Draw(dst, image.Rect(b.Min.X, b.Min.Y, b.Min.X+thickness, b.Max.Y), &image.Uniform{C: c}, image.Point{}, draw.Src)
	// Right
	draw.Draw(dst, image.Rect(b.Max.X-thickness, b.Min.Y, b.Max.X, b.Max.Y), &image.Uniform{C: c}, image.Point{}, draw.Src)
}

func rgba(img image.Image) *image.NRGBA {
	return imaging.Clone(img)
}

func drawRoundedRect(dst *image.NRGBA, rect image.Rectangle, radius int, fill color.Color) {
	// Desenha um retângulo simples + “máscara” de cantos arredondados com sobreposição — abordagem simples.
	// Para fins de marca d’água, isto é suficiente.
	draw.Draw(dst, rect, &image.Uniform{C: fill}, image.Point{}, draw.Over)
	// (para cantos realmente arredondados lisos, usar paths/vetor ou outra lib; mantemos simples)
	_ = radius
}

func parseTime(iso string) (string, error) {
	if strings.TrimSpace(iso) == "" {
		return "", nil
	}
	t, err := time.Parse(time.RFC3339, iso)
	if err != nil {
		// tenta formatos comuns
		if tt, e2 := time.Parse("2006-01-02 15:04:05", iso); e2 == nil {
			t = tt
		} else if tt, e3 := time.Parse("2006-01-02", iso); e3 == nil {
			t = tt
		} else {
			return "", err
		}
	}
	// Apresenta em fuso local do servidor
	return t.Local().Format("2006-01-02 15:04:05"), nil
}
func drawTextLines(dst *image.NRGBA, lines []string, x, y int, face font.Face, col color.Color, lineHeight int) error {
	// sombra
	shadow := image.NewUniform(color.RGBA{0, 0, 0, 140})
	dr := &font.Drawer{Dst: dst, Face: face}

	pt := fixed.P(x, y)
	for _, line := range lines {
		// sombra levemente deslocada
		dr.Dot, dr.Src = fixed.P(x+1, y+1), shadow
		dr.DrawString(line)
		// texto
		dr.Dot, dr.Src = pt, image.NewUniform(col)
		dr.DrawString(line)
		pt.Y += fixed.I(lineHeight)
		y += lineHeight
	}
	return nil
}

func faceFromBytes(fontData []byte, size float64) (font.Face, error) {
	ft, err := opentype.Parse(fontData)
	if err != nil {
		return nil, err
	}
	return opentype.NewFace(ft, &opentype.FaceOptions{
		Size:    size,
		DPI:     72,
		Hinting: font.HintingFull,
	})
}

func layoutPayloadBox(
	imgW, imgH int,
	face font.Face,
	rawLines []string,
) (box image.Rectangle, lines []string, textX, textY, lineH, padding int) {

	// Tamanho baseado na altura da imagem
	fontPx := max(14, imgH/60)
	lineH = int(float64(fontPx) + float64(fontPx)*0.33)
	padding = max(10, fontPx/2)
	margin := max(10, fontPx/2)

	// Largura máxima permitida p/ o texto (ex.: 45% da largura da imagem)
	maxTextW := int(float64(imgW) * 0.45)

	// Wrap linha a linha respeitando maxTextW
	var wrapped []string
	for _, s := range rawLines {
		// permite quebra manual com \n
		parts := strings.Split(s, "\n")
		for _, p := range parts {
			ws := wrapLines(face, p, maxTextW)
			wrapped = append(wrapped, ws...)
		}
	}

	// Encontra a maior largura real
	widest := 0
	for _, s := range wrapped {
		w := textWidthPx(face, s)
		if w > widest {
			widest = w
		}
	}

	textW := widest
	textH := lineH * len(wrapped)
	boxW := textW + padding*2
	boxH := textH + padding*2

	// Caixa âncorada no canto inferior-direito
	x2 := imgW - margin
	y2 := imgH - margin
	x1 := x2 - boxW
	y1 := y2 - boxH

	// Clamp: se por algum motivo ficou negativo, empurra pra dentro
	if x1 < margin {
		x1 = margin
		x2 = x1 + boxW
	}
	if y1 < margin {
		y1 = margin
		y2 = y1 + boxH
	}

	box = image.Rect(x1, y1, x2, y2)
	lines = wrapped
	textX = x1 + padding
	textY = y1 + padding + fontPx
	return
}

// normaliza a orientação de JPEzG com base no EXIF Orientation.
// Para PNG/sem EXIF, retorna como veio.
func normalizeOrientationJPEG(origBytes []byte, img image.Image, format string) image.Image {
	if strings.ToLower(format) != "jpeg" && strings.ToLower(format) != "jpg" {
		return img
	}
	x, err := exiflib.Decode(bytes.NewReader(origBytes))
	if err != nil || x == nil {
		return img // sem EXIF ou erro: mantém como está
	}
	tag, err := x.Get(exiflib.Orientation)
	if err != nil || tag == nil {
		return img
	}
	o, err := tag.Int(0)
	if err != nil {
		return img
	}

	// Mapeamento EXIF Orientation:
	// 1: Normal
	// 2: FlipH
	// 3: Rotate180
	// 4: FlipV
	// 5: Transpose (FlipH + Rotate90CW)
	// 6: Rotate90CW
	// 7: Transverse (FlipH + Rotate270CW)
	// 8: Rotate270CW
	switch o {
	case 2:
		return imaging.FlipH(img)
	case 3:
		return imaging.Rotate180(img)
	case 4:
		return imaging.FlipV(img)
	case 5:
		// aproxima Transpose: rotaciona 90° CW e espelha horizontal
		tmp := imaging.Rotate270(img) // 90° CW = Rotate270 (imaging é CCW)
		return imaging.FlipH(tmp)
	case 6:
		// 90° CW
		return imaging.Rotate270(img)
	case 7:
		// aproxima Transverse: rotaciona 270° CW (90° CCW) e espelha horizontal
		tmp := imaging.Rotate90(img) // 90° CCW
		return imaging.FlipH(tmp)
	case 8:
		// 270° CW (90° CCW)
		return imaging.Rotate90(img)
	default:
		return img
	}
}

func composeWatermark(base image.Image, p WebhookPayload, softwareLogo image.Image, clientLogo image.Image, fontBytes []byte) (image.Image, error) {
	dst := rgba(base)
	b := dst.Bounds()
	W, H := b.Dx(), b.Dy()

	// -----------------------------
	// 1) Moldura (linhas)
	// -----------------------------
	borderThickness := max(4, min(W, H)/800)                      // proporcional e discreto
	drawBorder(dst, borderThickness, color.RGBA{13, 31, 46, 255}) // #0D1F2E

	// -----------------------------
	// 2) Conteúdo (linhas de texto)
	// -----------------------------
	whenStr, _ := parseTime(p.PhotoTakenAt)
	gpsStr := ""
	if p.GPSLatitude != nil && p.GPSLongitude != nil {
		gpsStr = formatGPS(*p.GPSLatitude, *p.GPSLongitude) // ex.: "-26.304123,-48.846789"
	}

	linesRaw := []string{
		"Type: " + strings.TrimSpace(p.PhotoType),
		"Technician: " + strings.TrimSpace(p.UploadedBy),
	}
	if whenStr != "" {
		linesRaw = append(linesRaw, "Taken: "+whenStr)
	}
	if gpsStr != "" {
		// se quiser forçar quebra após a vírgula:
		// gpsStr = strings.Replace(gpsStr, ",", ",\n", 1)
		linesRaw = append(linesRaw, "GPS: "+gpsStr)
	}
	if s := strings.TrimSpace(p.DeviceInfo); s != "" {
		linesRaw = append(linesRaw, "Device: "+s)
	}

	// Tipografia base (proporcional à altura da imagem)
	fontSize := float64(max(14, H/60))
	face, err := faceFromBytes([]byte(fontBytes), fontSize)
	if err != nil {
		return nil, err
	}

	// Layout adaptativo da caixa (mede texto de verdade e faz wrap)
	boxRect, lines, textX, textY, lineH, _ := layoutPayloadBox(W, H, face, linesRaw)

	// Fundo da caixa (azul-escuro translúcido #0D1F2E A=160)
	drawRoundedRect(dst, boxRect, max(8, int(fontSize/1.2)), color.RGBA{13, 31, 46, 160})

	// Texto com sombra (legibilidade em qualquer fundo)
	_ = drawTextLines(dst, lines, textX+1, textY+1, face, color.RGBA{0, 0, 0, 140}, lineH)                       // sombra
	if err := drawTextLines(dst, lines, textX, textY, face, color.RGBA{255, 255, 255, 255}, lineH); err != nil { // branco
		return nil, err
	}

	// -----------------------------
	// 3) Logos (patch retrato/topo)
	// -----------------------------
	isPortrait := H > W

	// parâmetros ajustáveis
	topMarginPx := max(8, H/120)    // margem superior em retrato
	bottomMarginPx := max(6, H/130) // margem inferior em paisagem
	sideMarginPx := max(8, W/120)   // margem lateral mínima
	spacingPx := max(12, W/200)     // espaço entre logos
	landscapeLogoDiv := 18          // altura logo ~ H/18 em paisagem
	portraitLogoDiv := 22           // altura logo ~ H/22 em retrato (menor)
	portraitScale := 0.85           // encolhe ~15% adicional em retrato

	// calcula altura máxima das logos conforme orientação
	logoMaxH := H / landscapeLogoDiv
	if isPortrait {
		logoMaxH = int(float64(H/portraitLogoDiv) * portraitScale)
	}
	if logoMaxH < 28 {
		logoMaxH = 28 // piso mínimo
	}

	// prepara as logos (PNG com alpha recomendado)
	var logos []image.Image
	if p.WatermarkHasSoftwareLogo && softwareLogo != nil {
		logos = append(logos, imaging.Fit(softwareLogo, W, logoMaxH, imaging.Lanczos))
	}

	if p.WatermarkHasCompanyLogo && clientLogo != nil {
		logos = append(logos, imaging.Fit(clientLogo, W, logoMaxH, imaging.Lanczos))
	}

	if len(logos) > 0 {
		// mede largura total e altura máxima do conjunto
		totalW, maxH := 0, 0
		for _, lg := range logos {
			totalW += lg.Bounds().Dx()
			if h := lg.Bounds().Dy(); h > maxH {
				maxH = h
			}
		}
		if len(logos) >= 2 {
			totalW += spacingPx * (len(logos) - 1)
		}

		// Y: topo (retrato) ou base (paisagem)
		var y int
		if isPortrait {
			y = topMarginPx
		} else {
			y = H - maxH - bottomMarginPx
		}

		// X: centralizado com margem mínima
		x := (W - totalW) / 2
		if x < sideMarginPx {
			x = sideMarginPx
		}

		// desenha (usar Overlay e guardar retorno!)
		for i, lg := range logos {
			dst = imaging.Overlay(dst, imaging.Clone(lg), image.Pt(x, y), 1.0)
			x += lg.Bounds().Dx()
			if i < len(logos)-1 {
				x += spacingPx
			}
		}
	}

	return dst, nil
}

func formatGPS(lat, lon float64) string {
	return strings.TrimSpace(
		strings.ReplaceAll(
			strings.ReplaceAll(
				strings.TrimSpace(
					fmt.Sprintf("%.6f, %.6f", lat, lon),
				), "+", "",
			), " ", "",
		),
	)
}

func sprintf(format string, a ...any) string { return fmtSprintf(format, a...) }
func fmtSprintf(format string, a ...any) string {
	return (func() string { return fmt.Sprintf(format, a...) })()
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func main() {
	// Pequena gamb para evitar import direto de fmt no topo:
	_ = sprintf

	outputDir := envOr("OUTPUT_DIR", "./out")
	must(os.MkdirAll(outputDir, 0o755))

	softwareLogo, err := png.Decode(bytes.NewReader(softwareLogoBytes))
	if err != nil {
		log.Fatalf("failed to decode embedded software logo: %v", err)
	}

	r := gin.Default()

	r.POST("/image_watermark_service_webhook", func(c *gin.Context) {
		var p WebhookPayload
		if err := c.ShouldBindJSON(&p); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid JSON: " + err.Error()})
			return
		}

		// Carrega imagem base

		var (
			base image.Image
			err  error
		)

		switch {
		case strings.TrimSpace(p.ImageBase64) != "":
			base, _, err = loadImageFromBase64(p.ImageBase64)
		case strings.TrimSpace(p.ImageURL) != "":
			base, _, err = loadImageFromURL(p.ImageURL)
		default:
			err = errors.New("one of image_base64 or image_url must be provided")
		}
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "failed to load image: " + err.Error()})
			return
		}

		maxDim := 1600 // pode virar env (ex.: MAX_DIM)
		bw, bh := base.Bounds().Dx(), base.Bounds().Dy()
		if bw > maxDim || bh > maxDim {
			base = imaging.Fit(base, maxDim, maxDim, imaging.Lanczos)
		}

		if !p.AddWatermark {
			// retorna original (re-encoda em JPEG)
			var buf bytes.Buffer
			if err := jpeg.Encode(&buf, base, &jpeg.Options{Quality: 92}); err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "encode failed: " + err.Error()})
				return
			}
			c.Data(http.StatusOK, "image/png", buf.Bytes())
			return
		}

		// Carrega logo do cliente se solicitado
		var clientLogo image.Image
		if p.WatermarkHasCompanyLogo && strings.TrimSpace(p.CompanyLogoURL) != "" {
			img, err := loadImageFromURLIfPresent(p.CompanyLogoURL)
			if err != nil {
				// só loga; continua sem logo do cliente
				log.Println("WARN: falha ao carregar company_logo_url:", err)
			} else {
				clientLogo = img
			}
		}

		outImg, err := composeWatermark(base, p, softwareLogo, clientLogo, fontBytes)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "compose failed: " + err.Error()})
			return
		}

		// Salva e responde
		id := uuid.New().String()
		outPath := filepath.Join(outputDir, id+".png")
		f, err := os.Create(outPath)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create output: " + err.Error()})
			return
		}
		defer f.Close()
		if err := jpeg.Encode(f, outImg, &jpeg.Options{Quality: 92}); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "encode failed: " + err.Error()})
			return
		}

		// também devolve o binário na resposta
		var buf bytes.Buffer
		if err := jpeg.Encode(&buf, outImg, &jpeg.Options{Quality: 92}); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "encode failed: " + err.Error()})
			return
		}

		c.Header("X-Output-Path", outPath)
		c.Data(http.StatusOK, "image/png", buf.Bytes())
	})

	port := envOr("PORT", "8080")
	log.Println("listening on :" + port)
	must(http.ListenAndServe(":"+port, r))
}
