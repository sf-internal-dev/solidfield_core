package main

import (
	"bytes"
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
	"golang.org/x/image/font"
	"golang.org/x/image/font/opentype"
	"golang.org/x/image/math/fixed"
)

type WebhookPayload struct {
	ImageBase64             string   `json:"image_base64"`
	ImageURL                string   `json:"image_url"`
	PhotoType               string   `json:"photo_type"`
	UploadedBy              string   `json:"uploaded_by"`
	PhotoTakenAt            string   `json:"photo_taken_at"`
	AddWatermark            bool     `json:"add_watermark"`
	WatermarkHasCompanyLogo bool     `json:"watermark_has_company_logo"`
	GPSLatitude             *float64 `json:"gps_latitude"`
	GPSLongitude            *float64 `json:"gps_longitude"`
	DeviceInfo              string   `json:"device_info"`
	CompanyLogoURL          string   `json:"company_logo_url"`
}

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

func loadImageFromURL(url string) (image.Image, string, error) {
	client := &http.Client{
		Timeout: 15 * time.Second,
	}
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, "", err
	}
	// Alguns hosts exigem User-Agent e/ou Referer
	req.Header.Set("User-Agent", "CoreSF-ImageWatermarker/1.0 (+https://coresf.example)")
	req.Header.Set("Referer", url)

	resp, err := client.Do(req)
	if err != nil {
		return nil, "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode > 299 {
		// ajuda muito na depuração
		return nil, "", fmt.Errorf("fetch failed: status %d from %s", resp.StatusCode, url)
	}

	b, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, "", err
	}
	return decodeImage(b)
}

func textWidthPx(face font.Face, s string) int {
	d := &font.Drawer{Face: face}
	return int(d.MeasureString(s) >> 6) // converte 26.6 fix -> px
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

func decodeImage(b []byte) (image.Image, string, error) {
	// Tenta PNG
	if img, err := png.Decode(bytes.NewReader(b)); err == nil {
		return img, "png", nil
	}
	// Tenta JPEG
	if img, err := jpeg.Decode(bytes.NewReader(b)); err == nil {
		return img, "jpeg", nil
	}
	// Tenta genérico
	img, format, err := image.Decode(bytes.NewReader(b))
	return img, format, err
}

func loadImageFromBase64(s string) (image.Image, string, error) {
	// Permite base64 puro (sem prefixo data:)
	s = strings.TrimSpace(s)
	data, err := base64.StdEncoding.DecodeString(s)
	if err != nil {
		return nil, "", err
	}
	return decodeImage(data)
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

func faceFromTTF(ttfPath string, size float64) (font.Face, error) {
	fontBytes, err := os.ReadFile(ttfPath)
	if err != nil {
		return nil, err
	}
	fnt, err := opentype.Parse(fontBytes)
	if err != nil {
		return nil, err
	}
	face, err := opentype.NewFace(fnt, &opentype.FaceOptions{
		Size:    size,
		DPI:     96,
		Hinting: font.HintingFull,
	})
	if err != nil {
		return nil, err
	}
	return face, nil
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

func composeWatermark(base image.Image, p WebhookPayload, softwareLogo image.Image, clientLogo image.Image, fontPath string) (image.Image, error) {
	dst := rgba(base)
	b := dst.Bounds()
	W, H := b.Dx(), b.Dy()

	// Moldura (linhas)
	borderThickness := max(4, min(W, H)/800) // proporcional
	drawBorder(dst, borderThickness, color.RGBA{13, 31, 46, 255})

	// Logos na base (centro). Software logo sempre; client logo opcional.
	logoMaxH := max(32, H/18) // ~5-6% da altura
	spacing := max(12, W/200)

	var logos []image.Image
	if softwareLogo != nil {
		logos = append(logos, imaging.Fit(softwareLogo, W, logoMaxH, imaging.Lanczos))
	}
	if p.WatermarkHasCompanyLogo && clientLogo != nil {
		logos = append(logos, imaging.Fit(clientLogo, W, logoMaxH, imaging.Lanczos))
	}

	totalW := 0
	maxH := 0
	for _, lg := range logos {
		totalW += lg.Bounds().Dx()
		if lg.Bounds().Dy() > maxH {
			maxH = lg.Bounds().Dy()
		}
	}
	if len(logos) == 2 {
		totalW += spacing
	}

	yLogos := H - maxH - (borderThickness * 2) - 6
	xStart := (W - totalW) / 2

	xCursor := xStart
	for i, lg := range logos {
		logo := imaging.Clone(lg) // garante NRGBA com alpha
		dst = imaging.Overlay(dst, logo, image.Pt(xCursor, yLogos), 1.0)
		xCursor += lg.Bounds().Dx()
		if i == 0 && len(logos) == 2 {
			xCursor += spacing
		}
	}

	// Caixinha de info no canto inferior-direito
	// Conteúdo

	whenStr, _ := parseTime(p.PhotoTakenAt)
	gpsStr := ""
	if p.GPSLatitude != nil && p.GPSLongitude != nil {
		gpsStr = formatGPS(*p.GPSLatitude, *p.GPSLongitude)
	}
	lines := []string{
		"Type: " + strings.TrimSpace(p.PhotoType),
		"By: " + strings.TrimSpace(p.UploadedBy),
	}
	if whenStr != "" {
		lines = append(lines, "Taken: "+whenStr)
	}
	if gpsStr != "" {
		lines = append(lines, "GPS: "+gpsStr)
	}
	if strings.TrimSpace(p.DeviceInfo) != "" {
		lines = append(lines, "Device: "+strings.TrimSpace(p.DeviceInfo))
	}

	// Tipografia
	fontSize := float64(max(14, H/60))
	face, err := faceFromTTF(fontPath, fontSize)
	if err != nil {
		return nil, err
	}
	lineH := int(fontSize) + max(6, int(fontSize/3))
	// Calcula largura aproximada
	maxChars := 0
	for _, s := range lines {
		if len(s) > maxChars {
			maxChars = len(s)
		}
	}
	textW := int(float64(maxChars) * fontSize * 0.60) // heurística
	textH := lineH * len(lines)

	padding := max(10, int(fontSize/2))
	boxW := textW + padding*2
	boxH := textH + padding*2

	bw, bh := base.Bounds().Dx(), base.Bounds().Dy()
	wmScale := 2

	// cria layer transparente em 2× do tamanho da foto
	wm := imaging.New(bw*wmScale, bh*wmScale, color.NRGBA{0, 0, 0, 0})

	boxRect := image.Rect(W-boxW-borderThickness-10, H-boxH-borderThickness-10, W-borderThickness-10, H-borderThickness-10)
	// Render do texto em branco
	textX := boxRect.Min.X + padding
	textY := boxRect.Min.Y + padding + int(fontSize)
	// Fundo semi-transparente
	boxRect, lines, textX, textY, lineH, padding = layoutPayloadBox(bw, bh, face, lines)

	drawRoundedRect(wm, boxRect, 12*wmScale, color.RGBA{13, 31, 46, 160})

	err = drawTextLines(dst, lines, textX, textY, face, color.RGBA{255, 255, 255, 255}, lineH)
	if err != nil {
		return nil, err
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

	softwareLogoPath := os.Getenv("SOFTWARE_LOGO_PATH")
	if softwareLogoPath == "" {
		log.Println("WARN: SOFTWARE_LOGO_PATH não definido — a logo do software não será renderizada.")
	}
	fontPath := os.Getenv("FONT_PATH")
	if fontPath == "" {
		log.Fatal("Defina FONT_PATH para uma fonte TTF (ex.: ./assets/Inter-Regular.ttf)")
	}

	var softwareLogo image.Image
	if softwareLogoPath != "" {
		img, err := loadPNGFromPath(softwareLogoPath)
		if err != nil {
			log.Println("WARN: não consegui carregar SOFTWARE_LOGO_PATH:", err)
		} else {
			softwareLogo = img
		}
	}

	r := gin.Default()

	r.POST("/webhook", func(c *gin.Context) {
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

		outImg, err := composeWatermark(base, p, softwareLogo, clientLogo, fontPath)
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
