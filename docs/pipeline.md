# Pipeline do modelo

O pipeline treina um classificador XGBoost específico para cada espécie e usa
esse modelo para estimar o potencial codificante de novas sequências.

## Preparação

O dataset completo é um ZIP com pares CDS/ncRNA para as 16 espécies catalogadas:

```bash
rnamining prepare-data --input S5_File.zip --output data/
```

Para uma espécie aprovada, o ZIP deve conter na raiz:

```text
<species>.<assembly>.cds.all.fa.gz
<species>.<assembly>.ncrna.fa.gz
```

```bash
rnamining prepare-species --input Anolis_carolinensis.zip --output data/
```

O menor grupo define o número de amostras por classe. O pipeline balanceia,
embaralha e divide por classe em treino/teste. O padrão é 80%/20%; `--seed` e
`--train-ratio` controlam a reprodução.

Saídas principais:

```text
data/raw/
data/processed/train_test_split/coding/*_coding_train.fa
data/processed/train_test_split/noncoding/*_noncoding_train.fa
data/evaluation/*_test.fa
data/reports/*.csv
```

Os FASTAs de avaliação recebem `class:coding` ou `class:noncoding` no header.

## Features

Cada sequência é percorrida em triplets não sobrepostos, no frame zero. São
contados os 64 trinucleotídeos formados por `A`, `C`, `T` e `G`; triplets com
bases ambíguas ou inválidas são ignorados. Os contadores são normalizados pelo
número de bases válidas, produzindo uma matriz de 64 colunas.

## Treinamento

```bash
rnamining train --data data/processed/train_test_split \
  --output models/coding_prediction/
```

Para uma espécie:

```bash
rnamining train-species --data data/processed/train_test_split \
  --species Anolis_carolinensis --output models/coding_prediction/
```

Os modelos são serializados como pickle em `<species>.pkl`. Arquivos existentes
com o mesmo nome são substituídos.

## Predição e avaliação

```bash
rnamining predict --input sequences.fa \
  --organism Homo_sapiens --output outputs/prediction/
rnamining evaluate --output outputs/evaluation/current_models/
```

A avaliação usa os FASTAs mantidos em `data/evaluation/` e produz accuracy,
precision, recall, F1, MCC, AUROC, AUPRC e matriz de confusão. É uma avaliação
intraespécie, não um teste de generalização entre espécies.
