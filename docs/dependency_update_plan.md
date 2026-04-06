# Dependency Update Plan

## Objetivo
Atualizar as dependências do RNAMining preservando compatibilidade com a execução atual da ferramenta.

## Dependências atuais do projeto
1. Python >= 3.8
2. Pandas >= 0.23.3
3. Scikit-learn >= 0.21.3
4. XGBoost >= 1.2.0
5. Biopython >= 1.78

## Estratégia adotada
As dependências serão analisadas e atualizadas da menos sensível para a mais sensível, sempre comparando os resultados com o baseline gerado antes das alterações.
É considerado uma depêndencia sensível aquela que afeta diretamente a predição do modelo, interferindo no modelo, modificando a pipeline e modificando o output.

## Ordem de análise

### 1. Biopython
O Biopython é utilizado para a leitura de arquivos FASTA. As possíveis modificações decorrentes de sua atualização incluem mudanças na API ou falhas no parsing das sequências. No entanto, como essa biblioteca atua apenas na etapa de entrada dos dados, sem interferir diretamente no modelo ou nas predições, ela é considerada de baixa sensibilidade. Caso ocorra alguma quebra, ela tende a ser explícita, interrompendo a execução da ferramenta.

---

### 2. Scikit-learn
O Scikit-learn é utilizado apenas para embaralhamento de dados durante o treinamento, por meio da função shuffle. Os riscos associados à sua atualização estão relacionados a possíveis mudanças no comportamento dessa função ou em sua assinatura. Entretanto, como ele não participa diretamente da etapa de predição nem da manipulação do modelo salvo, seu impacto é limitado, sendo classificado como de baixa sensibilidade.

---

### 3. Pandas
O Pandas é utilizado para manipulação de dados, incluindo features, entradas e saídas intermediárias. A atualização dessa biblioteca pode introduzir mudanças na leitura e escrita de dados, alterações em tipos (dtype) e diferenças no comportamento de operações internas. Esses fatores podem afetar silenciosamente a estrutura dos dados utilizados pelo modelo, como a ordem das colunas ou o tipo numérico das features, impactando indiretamente a predição. Por esse motivo, o Pandas é considerado de média sensibilidade.

---

### 4. XGBoost
O XGBoost é a dependência mais sensível do RNAMining, pois está diretamente relacionado ao treinamento, ao carregamento do modelo salvo e ao comportamento final das predições. Diferentemente das demais bibliotecas, alterações em sua versão podem modificar o funcionamento da ferramenta mesmo quando o código continua executando normalmente, o que exige validação cuidadosa baseada em comparação com o baseline.

Um dos principais pontos de atenção é o uso de `pickle.load()` para recuperar modelos previamente treinados. O `pickle` não armazena apenas os parâmetros do modelo de forma independente; ele serializa o objeto Python completo, incluindo sua estrutura interna, atributos e a forma como a classe foi definida na versão da biblioteca utilizada no momento do salvamento. Dessa forma, ao atualizar o XGBoost, a classe `XGBClassifier` pode apresentar mudanças em atributos internos, nomes de variáveis ou na forma como o modelo é reconstruído. Isso pode levar a falhas explícitas durante o carregamento, como erros de atributo ou incompatibilidade de estrutura.

Entretanto, o cenário mais crítico não é a falha explícita, mas sim a quebra silenciosa. É possível que o modelo seja carregado sem erro aparente, porém interpretado de maneira diferente pela nova versão do XGBoost. Nesse caso, a ferramenta continua executando normalmente e gera saídas aparentemente válidas, mas o comportamento do modelo pode não ser equivalente ao original. Esse tipo de inconsistência é particularmente perigoso, pois não interrompe a execução e pode passar despercebido.

Além do carregamento do modelo, a atualização do XGBoost pode impactar diretamente o comportamento do método `predict()` utilizado no `RNAmining.py`. Como essa função depende da implementação interna da classe `XGBClassifier`, mudanças na biblioteca podem alterar a forma como as entradas são interpretadas, como o limiar de decisão é aplicado ou como as classes são atribuídas. Assim, mesmo que a interface da função permaneça a mesma, os rótulos gerados podem diferir dos obtidos anteriormente.

O mesmo se aplica ao método `predict_proba()`, caso utilizado. Pequenas variações numéricas nas probabilidades podem resultar em mudanças na classificação final, especialmente em casos próximos ao limiar de decisão. Isso pode impactar diretamente métricas como precisão, recall, F1-score e MCC, mesmo na ausência de erros explícitos.

Portanto, o XGBoost é classificado como de alta sensibilidade, exigindo validação rigorosa dos resultados após qualquer atualização.

### 5. Python
Pensar se vai ser atualizado junto ou deixado por último.

### Critério de aceitação

Uma atualização será considerada válida quando:

- não houver falhas na execução
- a estrutura dos dados for preservada
- as métricas permanecerem equivalentes ao baseline ou apresentarem variações justificáveis

Caso ocorram divergências significativas não explicadas, a atualização será considerada inválida e deverá ser revertida ou investigada.

---

### Observações

Deve-se ter atenção especial para possíveis quebras silenciosas, especialmente em dependências como o XGBoost, onde o modelo pode continuar sendo carregado e executado normalmente, mas gerar resultados diferentes sem indicação explícita de erro.

Por esse motivo, a validação não se baseia apenas na execução bem-sucedida, mas principalmente na equivalência dos resultados em relação ao baseline.