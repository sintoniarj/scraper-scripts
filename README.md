# Scraper Scripts

Scripts para web scraping utilizados pelo Scraper Panel.

## Uso

### Variáveis de Ambiente

- `TARGET_URL` - URL alvo para scraping (obrigatório)
- `JOB_ID` - ID do job no painel (opcional)
- `MAX_PAGES` - Número máximo de páginas (padrão: 10)
- `OUTPUT_DIR` - Diretório de saída (padrão: /tmp/scraper-output)

### Execução Direta

```bash
TARGET_URL="https://example.com" python3 scraper.py
```

### Via Bootstrap

```bash
TARGET_URL="https://example.com" JOB_ID="123" bash bootstrap.sh
```

## Output

O scraper gera os seguintes arquivos no diretório de saída:

- `progress.json` - Progresso atual do scraping
- `results.json` - Resultados finais
- `page_*.json` - Conteúdo de cada página scraped
