# App: Filehub

## Descrição
Responsável pelo gerenciamento, armazenamento e tratamento de arquivos enviados pelos usuários da plataforma, incluindo fotos de execução, assinaturas digitais, documentos PDF e outros anexos relacionados às Ordens de Serviço.


## Principais Funcionalidades
- Upload de arquivos por Técnicos em campo (via Mobile ou Web)

- Upload de assinaturas digitais do cliente

- Processamento e otimização de imagens (Exemplo: compressão, redimensionamento, marcação de data/hora)

- Armazenamento seguro de arquivos via Wasabi (utilizando django-storages + boto3)

- Controle de rastreabilidade de uploads (quem enviou, quando, de qual dispositivo)

- Integração com APIs de Hardware (câmera) via Mobile

- Gerenciamento de links e acessos a arquivos anexados a Ordens de Serviço

- Geração de URLs temporárias (signed URLs) para download seguro de arquivos, quando aplicável

- Validação de formatos, tamanhos e metadados durante o upload (Exemplo: bloqueio de formatos inválidos)


## Observação
Este app trabalhará fortemente em conjunto com o app de Ordem de Serviço e com o Painel Operacional, garantindo total rastreabilidade sobre os arquivos enviados.
Usuários de Permissão de Execução e Permissão de Coordenação terão acesso restrito apenas a uploads e visualização dos próprios arquivos ou dos arquivos vinculados às suas Ordens de Serviço.
Usuários com Permissão de Controle Total terão acesso administrativo a todos os arquivos da empresa.

