//go:build heif

package main

import (
	"bytes"
	"fmt"
	"image"
	"image/draw"
	"image/jpeg"
	"os"
	"os/exec"
	"runtime"

	"github.com/jdeng/goheif"
)

// heifDecode decodifica HEIC/AVIF usando goheif e retorna uma imagem
// copiada para *image.NRGBA* (memória 100% gerenciada pelo Go).
// Isso evita segfaults quando bibliotecas como "imaging" paralelizam leituras.
func heifDecode(b []byte) (image.Image, string, error) {
	// Protege contra possíveis panics vindos do CGO
	defer func() {
		_ = recover()
	}()

	imgC, err := goheif.Decode(bytes.NewReader(b))
	if err != nil {
		return nil, "", err
	}

	bnd := imgC.Bounds()
	dst := image.NewNRGBA(image.Rect(0, 0, bnd.Dx(), bnd.Dy()))
	draw.Draw(dst, dst.Bounds(), imgC, bnd.Min, draw.Src)

	// Garante que os objetos C não sejam coletados antes da cópia
	runtime.KeepAlive(imgC)
	runtime.KeepAlive(b)

	// “heic” aqui é um rótulo lógico; você pode usar "heif" se preferir
	return dst, "heic", nil
}

// heifToJPEGBytes tenta converter HEIC/AVIF -> JPEG.
// 1) tenta internamente (goheif -> NRGBA -> jpeg.Encode)
// 2) se falhar, cai no fallback externo via `heif-convert` (libheif-examples)
func heifToJPEGBytes(b []byte, quality int) ([]byte, error) {
	if jb, err := heifToJPEGBytesInternal(b, quality); err == nil {
		return jb, nil
	}
	return heifToJPEGBytesExternal(b, quality)
}

// heifToJPEGBytesInternal: caminho “puro Go” (com CGO), usando goheif.
func heifToJPEGBytesInternal(b []byte, quality int) ([]byte, error) {
	img, _, err := heifDecode(b)
	if err != nil {
		return nil, err
	}
	if quality <= 0 || quality > 100 {
		quality = 90
	}
	var buf bytes.Buffer
	if err := jpeg.Encode(&buf, img, &jpeg.Options{Quality: quality}); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// heifToJPEGBytesExternal: fallback usando o binário `heif-convert`.
// Requer: sudo apt-get install -y libheif-examples
func heifToJPEGBytesExternal(b []byte, quality int) ([]byte, error) {
	inFile, err := os.CreateTemp("", "wm_in_*.heic")
	if err != nil {
		return nil, err
	}
	defer os.Remove(inFile.Name())

	if _, err := inFile.Write(b); err != nil {
		inFile.Close()
		return nil, err
	}
	inFile.Close()

	outFile, err := os.CreateTemp("", "wm_out_*.jpg")
	if err != nil {
		return nil, err
	}
	outName := outFile.Name()
	outFile.Close()
	defer os.Remove(outName)

	// heif-convert não aceita “qualidade” por flag em todas as versões;
	// ele escolhe defaults bons. Se precisar controlar, pode converter para PNG
	// e depois JPEG você mesmo.
	cmd := exec.Command("heif-convert", inFile.Name(), outName)
	if out, err := cmd.CombinedOutput(); err != nil {
		return nil, fmt.Errorf("heif-convert failed: %v (%s)", err, string(out))
	}

	return os.ReadFile(outName)
}
