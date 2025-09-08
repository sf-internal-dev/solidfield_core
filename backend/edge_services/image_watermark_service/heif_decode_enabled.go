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
	// formato canônico (pode retornar "heic" ou "heif", aqui padronizo "heic")
	return img, "heic", nil
}
