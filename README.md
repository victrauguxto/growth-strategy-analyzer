# Growth Strategy Analyzer

Solução em Python para automatizar a análise de testes A/B de cashback do Méliuz. A aplicação lê um ou mais datasets, consolida os principais indicadores por variante, recomenda qual grupo deve ser escalado e gera um relatório HTML apresentável. Ao final, mantém um histórico CSV local e, quando as credenciais estão configuradas, registra o resultado diretamente na planilha indicada pelo `.env`.


## O que a aplicação faz

Para cada CSV encontrado na pasta `input/`, a aplicação:

1. converte datas e valores monetários para tipos adequados;
2. calcula o percentual médio de cashback, total de compradores, valor líquido e valor líquido por comprador de cada grupo;
3. recomenda a variante com o maior valor líquido total;
4. gera um relatório HTML com resumo executivo, tabela comparativa, gráfico e detalhamento por grupo;
5. registra a análise na primeira aba de uma planilha do Google Sheets;
6. adiciona o resultado a um histórico CSV local, independentemente da configuração do Google Sheets.

O valor líquido usado na decisão é calculado por:

```text
valor líquido = comissão - cashback
```

## Pré-requisitos

- [Git](https://git-scm.com/)
- Python 3.11 ou superior (Python 3.13 recomendado)
- Acesso à internet para instalar as dependências
- Acesso à internet ao abrir o relatório, pois os gráficos carregam o Chart.js por CDN
- Opcional: uma conta Google Cloud e uma Service Account para registrar resultados no Google Sheets

## Como clonar e instalar

Clone o repositório e entre na pasta do projeto:

```bash
git clone https://github.com/victrauguxto/growth-strategy-analyzer.git
cd growth-strategy-analyzer
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual.

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

No Linux ou macOS:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Como usar

### 1. Adicione os datasets

Crie a pasta `input/`, caso ela ainda não exista, e coloque nela os arquivos que deseja analisar:

```text
input/
├── dataset_01_parceiroA.csv
├── dataset_02_parceiroB.csv
└── dataset_03_parceiroC.csv
```

O programa processa, em uma única execução, todos os arquivos cujo nome corresponde a `dataset*.csv`. Recomenda-se seguir o formato `dataset_XX_nomeDoParceiro.csv`, pois o nome exibido no relatório é obtido a partir do nome do arquivo.

Cada CSV deve estar em UTF-8, usar vírgula como separador e conter exatamente estas colunas:

| Coluna | Tipo esperado | Descrição |
| --- | --- | --- |
| `Data` | `YYYY-MM-DD` | Data da observação |
| `Grupos de usuários` | texto | Variante do teste, como `Grupo 1` |
| `Parceiro` | texto | Parceiro analisado |
| `compradores` | inteiro | Usuários únicos que compraram no dia |
| `comissão` | moeda em reais | Comissão paga pelo parceiro ao Méliuz |
| `cashback` | moeda em reais | Cashback distribuído aos usuários |
| `vendas totais` | moeda em reais | GMV do dia |

Exemplo:

```csv
Data,Grupos de usuários,Parceiro,compradores,comissão,cashback,vendas totais
2011-01-01,Grupo 1,Parceiro A,196,R$ 10.273,R$ 3.267,R$ 93.390
```

Os valores monetários devem seguir o padrão brasileiro aceito pelo projeto, como `R$ 10.273` ou `R$ 10.273,50`.

### 2. Configure o registro dos resultados

A forma recomendada de usar o projeto é registrar cada análise diretamente no Google Sheets. O arquivo `.env.example` já contém o link da planilha original de acompanhamento. Para habilitar a integração, basta fornecer uma chave JSON de Service Account com acesso de edição a essa planilha e configurar o caminho da chave no `.env`.

Independentemente da integração, cada análise também é adicionada ao histórico local `data/test_results/test_results.csv`.

#### Opção recomendada: escrever na planilha original

1. Coloque o arquivo JSON de credenciais da Service Account na pasta `credentials/`. Por exemplo:

   ```text
   credentials/credenciais-google.json
   ```

2. Copie o arquivo de configuração de exemplo.

   No Windows PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

   No Linux ou macOS:

   ```bash
   cp .env.example .env
   ```

3. No `.env`, substitua somente o valor de `GOOGLE_APPLICATION_CREDENTIALS` pelo caminho do arquivo JSON. Mantenha `GOOGLE_SHEETS_SPREADSHEET_URL` com o link que já veio no `.env.example`:

   ```dotenv
   GOOGLE_APPLICATION_CREDENTIALS=credentials/credenciais-google.json
   GOOGLE_SHEETS_SPREADSHEET_URL=<link já fornecido no .env.example>
   ```

4. Confirme que o e-mail do campo `client_email` da chave JSON possui permissão de edição na planilha.

5. Execute `python main.py`. Para cada dataset processado, o sistema adicionará uma nova linha à primeira aba da planilha indicada em `GOOGLE_SHEETS_SPREADSHEET_URL`.

A primeira aba deve conter estes cabeçalhos:

```text
Nome do teste | Data / Hora Execução | Descrição | Resultado | Decisão tomada
```

Se quiser usar outra planilha, substitua `GOOGLE_SHEETS_SPREADSHEET_URL`, compartilhe a nova planilha com o `client_email` da Service Account e mantenha os mesmos cabeçalhos.

Para criar credenciais próprias, crie uma Service Account no Google Cloud e habilite as APIs Google Sheets e Google Drive. A chave precisa estar no formato JSON.

Nunca publique o `.env` nem a chave JSON da Service Account. A pasta `credentials/`, o `.env` e os arquivos JSON estão configurados para não serem versionados pelo Git.

#### Opção alternativa: usar somente o CSV local

Não é necessário criar um arquivo `.env`. Execute diretamente a aplicação e o histórico CSV será criado automaticamente. As próximas execuções acrescentam novas linhas ao mesmo arquivo, sem apagar os resultados anteriores.

### 3. Execute a análise

Na raiz do projeto, com o ambiente virtual ativo, execute:

```bash
python main.py
```

Exemplo de saída no terminal:

```text
Processing arquivo: dataset_01_parceiroA.csv
Relatório gerado em: .../output/dataset_01_parceiroA_report.html
Google Sheets não configurado. Resultado mantido em: data/test_results/test_results.csv
Processamento finalizado. 1 arquivo(s) processado(s).
```

### 4. Consulte os resultados

Os relatórios são gravados em:

```text
output/<nome_do_dataset>_report.html
```

Abra o arquivo HTML em um navegador. Cada relatório contém:

- resumo executivo do teste;
- variante recomendada e justificativa;
- comparação dos KPIs por grupo;
- gráfico de performance relativa;
- detalhamento e observações por variante.

Cada teste executado localmente acrescenta uma linha ao arquivo:

```text
data/test_results/test_results.csv
```

O cabeçalho é criado somente na primeira execução e os resultados anteriores são preservados. Quando o Google Sheets estiver configurado e acessível, a mesma linha também será adicionada à primeira aba da planilha; o histórico local continuará armazenado.

## Estrutura do projeto

```text
growth-strategy-analyzer/
├── main.py                    # Orquestra a análise de todos os datasets
├── requirements.txt           # Dependências Python
├── .env.example               # Exemplo de configuração do Google Sheets
├── input/                     # CSVs que serão analisados
├── output/                    # Relatórios HTML gerados
├── data/test_results/         # Histórico CSV cumulativo das execuções
├── credentials/               # Chaves locais do Google (não versionadas)
└── utils/
    ├── csv_reader.py           # Leitura, tratamento e cálculo dos KPIs
    ├── graph_builder.py        # Gráfico interativo em Chart.js
    ├── html_generator.py       # Recomendação e geração do relatório
    └── sheets_client.py        # Persistência no Sheets ou em CSV
```

## Critério de recomendação

A variante recomendada é aquela com o maior **valor líquido total** no período. Se ela também tiver o maior valor líquido por comprador, essa informação é incluída na justificativa.

Os principais indicadores apresentados são:

- percentual médio de cashback sobre as vendas;
- total de compradores;
- valor líquido total;
- valor líquido por comprador.

O relatório compara os resultados observados. Ele não calcula significância estatística e a recomendação não deve ser interpretada automaticamente como uma projeção linear para 100% do tráfego.

## Solução de problemas

### Nenhum CSV foi encontrado

Confirme que os arquivos estão na pasta `input/`, começam com `dataset` e terminam com `.csv`.

### Erro ao ler as colunas

Verifique a codificação UTF-8, o separador por vírgulas e os nomes exatos descritos na seção de schema. Acentos fazem parte dos nomes esperados.

### O resultado não foi enviado ao Sheets

A aplicação preserva automaticamente o resultado no histórico CSV local. Verifique:

- as duas variáveis do `.env`;
- o caminho para a chave JSON;
- se a planilha foi compartilhada com o `client_email` da Service Account;
- se as APIs Google Sheets e Google Drive estão habilitadas;
- se a Service Account possui permissão de edição.

### O gráfico não aparece no relatório

Conecte-se à internet ao abrir o HTML, pois o Chart.js é carregado de `cdn.jsdelivr.net`.
