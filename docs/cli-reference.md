# CLI

## Instalação

```bash
conda env create --file environment.yml
conda activate rnamining
python -m pip install -e .
```

```bash
rnamining --help
rnamining <comando> --help
```

Todos os caminhos relativos são resolvidos a partir do diretório atual.

## Comandos

### Compatibilidade com PULPOSEQ

A interface de predição usada pelo PULPOSEQ é suportada diretamente:

```bash
rnamining -f sequences.fa \
  -organism_name Homo_sapiens \
  -prediction_type coding_prediction \
  -output_folder outputs/prediction/
```

Ela gera `predictions.txt`, `codings.txt` e `noncodings.txt` no diretório
indicado. O comando moderno `rnamining predict ...` continua disponível.

### `prepare-data`

Prepara o ZIP completo de 16 espécies:

```bash
rnamining prepare-data --input S5_File.zip --output data/ \
  [--seed 42] [--train-ratio 0.8]
```

`--train-ratio` deve estar estritamente entre 0 e 1.

### `prepare-species`

Prepara uma espécie aprovada a partir de um ZIP com exatamente os dois arquivos
`.cds.all.fa.gz` e `.ncrna.fa.gz` na raiz:

```bash
rnamining prepare-species --input species.zip --output data/ \
  [--seed 42] [--train-ratio 0.8]
```

### `train` e `train-species`

```bash
rnamining train --data data/processed/train_test_split \
  --output models/coding_prediction/ [--seed 42]

rnamining train-species --data data/processed/train_test_split \
  --species Homo_sapiens --output models/coding_prediction/ [--seed 42]
```

O primeiro treina todos os pares disponíveis; o segundo treina apenas a
espécie informada. Ambos escrevem `<species>.pkl` e podem substituir arquivos
existentes.

### `predict`

```bash
rnamining predict --input sequences.fa --organism Homo_sapiens \
  --output outputs/prediction/ \
  [--models models/coding_prediction] \
  [--prediction-type coding_prediction]
```

`--models` aponta para o diretório que contém `<organism>.pkl`. Sem essa opção,
o padrão é o diretório de modelos do repositório; `RNAMINING_MODEL_DIR` também
pode configurar esse padrão. O FASTA deve ter headers `>` e sequência não vazia.

Saídas: `predictions.txt`, `codings.txt`, `noncodings.txt` e
`edited_file.fasta`.

### `evaluate`

```bash
rnamining evaluate --output outputs/evaluation/current_models/
```

Opções adicionais: `--models`, `--tests`, `--species` (repetível),
`--evolutionary-group`, `--distance-group`, `--seed` e `--repetition`. Por
padrão, exige modelo e FASTA de teste para todas as espécies.

Saídas: `metrics_current_models.csv` e
`metrics_current_models_summary.csv`.

## Erros

Os comandos falham quando arquivos necessários estão ausentes, FASTA/ZIP é
inválido, a espécie não é catalogada ou o modelo não existe. Diretórios de
saída são criados automaticamente.
