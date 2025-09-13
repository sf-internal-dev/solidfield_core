//go:build !heif

package main

import (
	"errors"
)

func heifToJPEGBytes(_ []byte, _ int) ([]byte, error) {
	return nil, errors.New("heif disabled at build time (compile with -tags heif)")
}
