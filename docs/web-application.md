# Aplicação web

## Execução local

```bash
cp .env.exemple .env
mkdir -p runtime/jobs
sudo chown -R 33:33 runtime
docker compose -f compose.local.yaml up --build -d
```

Acesse <http://localhost/>. Diagnóstico e desligamento:

```bash
docker compose -f compose.local.yaml ps
docker compose -f compose.local.yaml logs
docker compose -f compose.local.yaml down
```

O arquivo local publica a porta 80. Para um reverse proxy existente, use
`compose.proxy.yaml`; ele requer a rede externa `gatewayapps_proxy` e o proxy
deve encaminhar para `rnamining_webserver:80`.

## Fluxo de uma análise

1. O usuário envia `.txt`, `.fasta` ou `.fa` pela página de análise.
2. `api/upload.php` aceita no máximo 20 MiB e salva o FASTA em
   `runtime/jobs/<id>/input/sequences.fasta`.
3. `api/predict.php` valida a espécie e executa a CLI Python de forma síncrona.
4. Resultados ficam em `runtime/jobs/<id>/output/` e logs em `logs/`.
5. `results.php` mostra `predictions.txt`; downloads são feitos pela API.

Downloads permitidos: `RNAmining.zip`, `predictions.txt`, `codings.txt` e
`noncodings.txt`. O ZIP contém os três arquivos principais de resultado.

## Configuração e segurança

O PHP usa `RNAMINING_PROJECT_DIR`, `RNAMINING_RUNTIME_DIR` e
`RNAMINING_PYTHON`. No Compose, os valores são `/opt/rnamining`,
`/opt/rnamining/runtime` e `/opt/conda/envs/rnamining/bin/python`.

O ID do job precisa ter 32 caracteres hexadecimais. O download aceita somente
nomes fixos, reduzindo risco de traversal. A aplicação não fornece
autenticação, autorização, expiração ou remoção automática de jobs; uma
implantação pública precisa adicionar essas políticas e definir retenção para
uploads e logs.

Se o PHP não puder escrever em `runtime/`, corrija a propriedade/permissão do
diretório para o UID/GID usado pelo PHP-FPM. Em WSL, confirme a integração do
Docker Desktop antes de executar `docker compose`.
