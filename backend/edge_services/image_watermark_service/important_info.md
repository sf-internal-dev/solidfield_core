sudo apt-get update
sudo apt-get install -y libheif-dev libde265-dev libx265-dev pkg-config

# build com HEIC habilitado
CGO_ENABLED=1 go build -tags heif -o image_watermark_service .
./image_watermark_service

# Isso aqui é para o ambiente de produção
# para habilitar CGO e dar suporte a arquivos .heif vindos de dispositivos IOS

CGO_ENABLED=1 go build -tags heif -o watermark .
