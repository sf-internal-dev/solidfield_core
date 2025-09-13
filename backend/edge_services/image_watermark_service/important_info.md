sudo apt-get update
sudo apt-get install -y libheif-dev libde265-dev libx265-dev pkg-config

# build com HEIC habilitado
CGO_ENABLED=1 go build -tags heif -o image_watermark_service .
./image_watermark_service

# Isso aqui é para o ambiente de produção
# para habilitar CGO e dar suporte a arquivos .heif vindos de dispositivos IOS

CGO_ENABLED=1 go build -tags heif -o watermark .

# CURL command to generate a watermarked picture
curl -v -X POST http://localhost:8080/image_watermark_service_webhook   -H "Content-Type: application/json"   -o result.jpg   -d '{
    "image_url": "http://127.0.0.1:8081/foto.heic",
    "photo_type": "installation",
    "uploaded_by": "Adryan",
    "photo_taken_at": "2025-09-02T18:37:00Z",
    "add_watermark": true,
    "watermark_has_company_logo": false,
    "watermark_has_software_logo": true,
    "device_info": "Pixel 7"
  }'