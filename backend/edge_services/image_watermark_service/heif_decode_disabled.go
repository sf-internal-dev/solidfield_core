//go:build !heif

package main

import (
	"errors"
	"image"
)

func heifDecode(_ []byte) (image.Image, string, error) {
	return nil, "", errors.New("heif support not built (use: go run -tags heif .)")
}
