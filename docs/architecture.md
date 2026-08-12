# Arquitetura

RNAmining possui três camadas principais:

```text
FASTA → preparação/features → modelo XGBoost → resultados
                              ↑
                    models/<organismo>.pkl
```

## Código científico

- `src/rnamining/fasta.py`: leitura, validação e escrita de FASTA.
- `src/rnamining/features.py`: frequências dos 64 trinucleotídeos.
- `src/rnamining/data_preparation.py`: extração, balanceamento e split.
- `src/rnamining/training.py`: treinamento por espécie.
- `src/rnamining/inference.py`: carregamento e predição.
- `src/rnamining/evaluation.py`: métricas e CSVs.
- `src/rnamining/cli.py`: interface dos fluxos.

Os modelos versionados ficam em `models/coding_prediction/<species>.pkl`.
Cada espécie possui um modelo próprio; o organismo informado determina o
arquivo carregado.

## Aplicação web

Nginx expõe apenas `web/public/` e encaminha PHP para PHP-FPM. O fluxo é
síncrono:

1. `api/upload.php` valida extensão/tamanho e salva o FASTA.
2. `api/predict.php` valida a espécie e executa `python -m rnamining.cli predict`.
3. `results.php` lê `predictions.txt`.
4. `api/download.php` libera somente arquivos de resultado conhecidos.

Cada execução usa `runtime/jobs/<id>/{input,output,logs}`. Não há fila,
autenticação, expiração ou limpeza automática de jobs.

## Containers e volumes

`compose.local.yaml` publica a aplicação na porta 80. `compose.proxy.yaml`
usa a rede Docker externa `gatewayapps_proxy`. O container PHP monta o projeto
em `/opt/rnamining` e o runtime em `/opt/rnamining/runtime`; Nginx recebe
somente os arquivos públicos em modo somente leitura.

Dados gerados em `data/`, `outputs/` e `runtime/jobs/` não são artefatos de
código. Para auditoria, preserve commit, comando, parâmetros, entrada e
checksum do modelo.
