# CLI Docker

A imagem Docker empacota o ambiente Conda, o código e os modelos versionados.
Não é necessário instalar Python ou Conda no host.

## Construir

Na raiz do repositório:

```bash
docker build -f docker/cli/Dockerfile -t rnamining:1.0.4 .
```

O `Dockerfile` usa Debian, Miniforge Linux x86-64 e as versões declaradas em
`environment.yml`.

## Executar diretamente

```bash
docker run --rm \
  -v "$PWD:/work" -w /work \
  rnamining:1.0.4 predict \
  --input /work/sequences.fa \
  --organism Homo_sapiens \
  --output /work/outputs/prediction
```

O entrypoint já é `rnamining`. Preparação, treinamento e avaliação usam a
mesma forma de chamada. Os modelos internos da imagem são usados por padrão.

## Wrapper do projeto

`bin/rnamining` monta o diretório atual em `/work`, define o diretório de
trabalho e executa o container com o UID/GID do usuário atual:

```bash
chmod +x bin/rnamining
bin/rnamining predict \
  --input tests/fixtures/anolis_regression.fa \
  --organism Anolis_carolinensis \
  --output outputs/docker-prediction
```

Para usar outra tag:

```bash
RNAMINING_DOCKER_IMAGE=rnamining:1.0.4 bin/rnamining --help
```

Arquivos escritos em caminhos relativos aparecem no host montado em `/work`.
A imagem atual é construída para Linux x86-64.
