import pandas as pd

# Carregar dados atualizados
df_estoque = pd.read_csv('bases_exemplos/estoque_exemplo.csv')
df_ordens = pd.read_csv('bases_exemplos/ordens_exemplo.csv')

print('NOVAS Capacidades por produto:')
caps = df_estoque.groupby('Produto')['Quantidade_Disponivel'].sum()
print(caps)

print('\nDemandas por produto:')
dems = df_ordens.groupby('Produto')['Quantidade'].sum()
print(dems)

print('\nViabilidade:')
for produto in caps.index:
    cap = caps[produto]
    dem = dems.get(produto, 0)
    viavel = cap >= dem
    print(f'{produto}: Cap={cap}, Dem={dem}, Viável={viavel}')
