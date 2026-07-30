# Walkthrough: Otimização do Cadastro e Inclusão de Dados Demográficos

O formulário de cadastro principal foi atualizado para simplificar a entrada de dados obrigatórios, garantindo ao mesmo tempo uma coleta mais rica de dados demográficos de forma opcional.

## 📋 Alterações Realizadas

### 1. Remoção do Telefone
O campo **Telefone** foi permanentemente removido tanto da interface visual quanto das rotinas de banco de dados no momento da criação da conta. Isso reduz a fricção, permitindo que o pesquisador crie a conta preenchendo menos campos obrigatórios. O bug de validação relacionado a esse campo que impedia a conclusão do cadastro também foi eliminado.

### 2. Opção Vazia para "Vínculo Institucional"
Anteriormente, o sistema pré-selecionava a primeira universidade da lista automaticamente. Para evitar que pesquisadores acabassem enviando vínculos incorretos sem perceber, inserimos uma **opção vazia (Selecione...)** no topo da lista. O usuário precisará interagir com o campo para escolher sua universidade correta ou escolher "Outra Instituição".

### 3. Inclusão de Novos Campos Opcionais
Adicionamos 3 novas opções não-obrigatórias para traçar um perfil demográfico do pesquisador, enriquecendo o banco de dados e as análises da plataforma:
* **Idade:** (Campo numérico ajustável de 0 a 120).
* **Sexo:** Opções suspensas (`Masculino`, `Feminino`, `Não informar`).
* **Raça/Etnia:** Opções suspensas (`Branca`, `Parda`, `Preta`, `Indígena`, `Outra`).

### 4. Integração no Backend (Firestore e CSV)
Essas 3 novas métricas (Idade, Sexo, Raça/Etnia) agora são passadas via backend durante a função `cadastrar_usuario()`. O modelo de dados interno e as coleções no Firebase foram expandidas e receberão adequadamente essas variáveis sempre que o pesquisador optar por preenchê-las.
