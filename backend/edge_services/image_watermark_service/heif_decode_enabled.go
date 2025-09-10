//go:build heif

package main

import (
	"bytes"
	"image"

	"github.com/jdeng/goheif"
)

func heifDecode(b []byte) (image.Image, string, error) {
	// Tenta decodificar HEIC/HEIF com libheif (requer CGO + libheif)
	img, err := goheif.Decode(bytes.NewReader(b))
	if err != nil {
		return nil, "", err
	}

	// >>> CÓPIA PROFUNDA PARA MEMÓRIA GO <<<
	imgNRGBA := cloneToNRGBA(img)
	return imgNRGBA, "heic", nil

}
