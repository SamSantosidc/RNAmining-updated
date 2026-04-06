## Estado real das dependências em ambiente limpo (Python 3.8)

Embora o README original documente versões mínimas antigas, uma instalação limpa do pacote `rnamining`, pelo conda, em Python 3.8 atualmente resolve as seguintes versões:

- Biopython 1.83
- Pandas 2.0.3
- Scikit-learn 1.3.2
- XGBoost 1.2.0

Dessa forma, Biopython, Pandas e Scikit-learn foram considerados já atualizados. A atualização controlada a ser avaliada passa a se concentrar no XGBoost.

## XGBoost Update Log

### Ambiente
- Python 3.8
- RNAMining baseline funcional com XGBoost 1.2.0

---

### Atualização do XGBoost

A dependência XGBoost foi atualizada de:

- 1.2.0 → 2.0.3

### fix: erro ao carregar modelo por caminho relativo

O erro ocorria porque o RNAMining utilizava um caminho relativo para carregar os modelos `.pkl`:

`models/coding_prediction/<organism>.pkl`

Esse tipo de caminho depende do diretório atual de execução (cwd). Como o script estava sendo executado via notebook/subprocess, o diretório não era o esperado, fazendo com que o modelo não fosse encontrado.

#### Mudanças para consertar

A solução foi utilizar um caminho absoluto baseado na localização do próprio script, utilizando `Pathlib` e `__file__`. Dessa forma, o modelo é localizado corretamente independentemente de onde o script é executado.

Antes:
```python
model = pickle.load(open('models/' + 'coding_prediction/' + organism_name + '.pkl', 'rb'))

Depois:

from pathlib import Path

base_dir = Path(__file__).resolve().parent
model_path = base_dir / "models" / "coding_prediction" / f"{organism_name}.pkl"

model = pickle.load(open(model_path, 'rb'))
```

---

#  2. Fix do XGBoost

### fix: incompatibilidade entre modelos .pkl e nova versão do XGBoost

Após a atualização do XGBoost de 1.2.0 para 2.0.3, o RNAMining passou a falhar ao carregar os modelos, apresentando o erro:

`AttributeError: Can't get attribute 'XGBoostLabelEncoder'`

Isso ocorre porque os modelos `.pkl` foram gerados utilizando uma versão antiga do XGBoost. Ao tentar carregá-los com a versão nova, o `pickle` não consegue reconstruir corretamente o objeto, pois a estrutura interna da biblioteca mudou.

Ou seja, o modelo espera objetos da versão antiga, mas o XGBoost atual não reconhece mais esses mesmos componentes.

#### Mudanças para consertar

Como o objetivo é atualizar a ferramenta, a solução adotada foi retreinar os modelos.

Os novos modelos serão gerados utilizando o XGBoost 2.0.3

Para isso, serão utilizados os dados, de cada espécie, mais recente do ensemble, gerando novos arquivos `.pkl` que poderão ser carregados corretamente na versão atualizada.