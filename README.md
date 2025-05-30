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

