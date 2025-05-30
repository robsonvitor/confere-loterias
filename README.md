# O que este script faz

1. Ele conecta ao webservice da caixa e faz o download dos resultados das loterias e concursos, conforme definido no banco de dados;
2. Confere os resultados com os números apostados;
3. Caso tenha acertos, ele envia uma mensagem para o Telegram, conforme definido no arquivo settings.json;
4. Se o campo ```DEBUG``` estiver como ```true``` no arquivo ```settings.json```, o script imprime os resultados no terminal.

### Criar o virtualenv
```bash
python3 -m venv venv_loterias
```

### Ativar
```bash
source venv_loterias/bin/activate
```
## Instalar as dependências no venv
```bash
pip install -r requirements.txt
```

## Renomeie o arquivo settings.json e preencha com as suas variáveis;
```bash
mv -i settings.example.json settings.json
```

## Executar a aplicação 

```bash
python3 app.py
```

1. Na primeira execução será criado o banco;
2. Após criado o banco, acesse ele e insira os dados das apostas;
3. Execute novamente para realizar a conferência dos concursos apostados.


# Sugestões:
1. colocar para executar via crontab uma vez ao dia (se ficar consultando demais o webservice, será bloqueado pelos sistemas de segurança da Caixa);
2. Visualizador para bancos SQLite: dbeaver-ce.
