//go:build heif

package main

import (
	"bytes"
	"image"
	"image/draw"
	"image/jpeg"
	"os"
	"os/exec"
	"runtime"

	"github.com/jdeng/goheif"
)

// Tenta decodificar HEIF/AVIF em memória e re-encoda para JPEG (qualidade configurável).
func heifToJPEGBytesInternal(b []byte, quality int) ([]byte, error) {
	// proteje contra panics vindos de CGO
	defer func() { _ = recover() }()

	imgC, err := goheif.Decode(bytes.NewReader(b))
	if err != nil {
		return nil, err
	}
	// deep copy -> memória Go
	srcB := imgC.Bounds()
	nrgba := image.NewNRGBA(image.Rect(0, 0, srcB.Dx(), srcB.Dy()))
	draw.Draw(nrgba, nrgba.Bounds(), imgC, srcB.Min, draw.Src)

	// garante que os objetos C não sejam coletados antes da cópia
	runtime.KeepAlive(imgC)
	runtime.KeepAlive(b)

	// encode para JPEG
	var out bytes.Buffer
	if quality <= 0 || quality > 100 {
		quality = 90
	}
	if err := jpeg.Encode(&out, nrgba, &jpeg.Options{Quality: quality}); err != nil {
		return nil, err
	}
	return out.Bytes(), nil
}

// Fallback externo usando o utilitário `heif-convert`.
// Requer: sudo apt-get install -y libheif-examples
func heifToJPEGBytesExternal(b []byte, quality int) ([]byte, error) {
	dir := os.TempDir()
	in, err := os.CreateTemp(dir, "wm_in_*.heic")
	if err != nil {
		return nil, err
	}
	defer os.Remove(in.Name())
	if _, err := in.Write(b); err != nil {
		in.Close()
		return nil, err
	}
	in.Close()

	out, err := os.CreateTemp(dir, "wm_out_*.jpg")
	if err != nil {
		return nil, err
	}
	outName := out.Name()
	out.Close()
	defer os.Remove(outName)

	// `heif-convert in.heic out.jpg` (ele escolhe qualidade boa por padrão)
	cmd := exec.Command("heif-convert", in.Name(), outName)
	// opcional: cmd.Stdout = io.Discard; cmd.Stderr = io.Discard
	if err := cmd.Run(); err != nil {
		return nil, err
	}
	return os.ReadFile(outName)
}

// Converte HEIF/AVIF -> JPEG. Tenta interno, cai para externo se precisar.
func heifToJPEGBytes(b []byte, quality int) ([]byte, error) {
	if jb, err := heifToJPEGBytesInternal(b, quality); err == nil {
		return jb, nil
	}
	// fallback externo (instale libheif-examples)
	return heifToJPEGBytesExternal(b, quality)
}
