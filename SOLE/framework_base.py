
import os
import re
registro_global_elementos = []

def registrar_elemento(cls):
    registro_global_elementos.append(cls())
    return cls

class BlackboardBase:
    pass

class ElementoBase:
    def __init__(self, id_name):
        self.id_name = id_name
        self.prioridade = 0
        self.is_core = False
        self.is_permissive = False

    def condicao(self, blackboard):
        return False

    def acao(self, blackboard):
        pass

## --------------> INTERPRETADOR - ele le o arquivo .slel e definir as prioridades e tipos de cada elemento
class Interpretador:

    @staticmethod
    def carregar_e_aplicar_configuracoes(caminho_arquivo):
        
        # ------------ PRE-PROCESSAMENTO ------------- #
        variaveis_internas = {}

        #caminho do arquivo .slel
        diretorio_atual = os.path.dirname(__file__)
        caminho_absoluto = os.path.join(diretorio_atual, caminho_arquivo)
        
        with open(caminho_absoluto, 'r', encoding='utf-8') as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if linha.startswith('#config'):
                    blocos_encontrados = re.findall(r'\[(.*?)\]', linha)
                    for bloco in blocos_encontrados:
                        partes = bloco.split(':')
                        if len(partes) == 2:
                            chave = partes[0].strip()
                            valor = partes[1].strip()
                            variaveis_internas[chave] = valor
                        else:
                            print(f"[Parabens, VOCÊ CONSEGUIU errar no arquivo config, aqui seu erro: [{bloco}]")

        ordem_leitura = variaveis_internas.get('ordem', '-')
        espaco_de_prioridade = int(variaveis_internas.get('espaco_de_prioridade', 10))

        # ------------ PROCESSAMENTO DOS ELEMENTOS ------------- #
        variaveis_internas.clear() 

        #Valor da prioridade de cada elemento (Caso eu leia de cima para baixo, o elemento mais a cima vai ter a prioridade 0 [Menor], caso eu leia de baixo para cima, o elemento mais a cima tera a maior priorirdade)
        prioridade_atual = 0
        arquivo_open = None

        with open(caminho_absoluto, 'r', encoding='utf-8') as arquivo:
            
            if ordem_leitura == '-':
                arquivo_open = arquivo.readlines()
            elif ordem_leitura == '+':
                arquivo_open = reversed(arquivo.readlines())
            
            if arquivo_open is None:
                arquivo_open = arquivo.readlines() # Fallback de segurança

            for linha in arquivo_open:
                linha = linha.strip()
                if not linha or not linha.startswith('@'):
                    continue

                partes = linha.split('->')
                if len(partes) != 2:
                    continue #Bons habitos para evitar erros
                
                nome_elemento = partes[0].replace('@', '').strip()
                bloco_regras = partes[1].strip()
                regras_do_elemento = {}

                # Salvando a prioridade de cada elemento
                regras_do_elemento['prioridade_calculada'] = prioridade_atual
                
                colchetes_encontrados = re.findall(r'\[(.*?)\]', bloco_regras)
                for colchete in colchetes_encontrados:
                    sub_partes = colchete.split(':')
                    if len(sub_partes) == 2:
                        regras_do_elemento[sub_partes[0].strip()] = sub_partes[1].strip()

                variaveis_internas[nome_elemento] = regras_do_elemento
                
                #Mudando o valor da prioridade para o próximo elemento
                prioridade_atual += espaco_de_prioridade 

        # ------------ INJEÇÃO NAS CLASSES ------------- #
        #Objetivo: Andar por todos os elementos criador e injetar as informaçoes dentro deles

        for elemento in registro_global_elementos:
            nome_codigo = elemento.id_name # O nome que você definiu no super().__init__
            
            if nome_codigo in variaveis_internas:
                regras_extraidas = variaveis_internas[nome_codigo]
                
                #Aplicando a prioridade
                elemento.prioridade = regras_extraidas['prioridade_calculada']
                
                #Aplicando se é true ou false a partir do simbolo + ou - ( talvez trocar para 0 e 1 ou true e false kkkk parece mais intuitivo)
                if 'core' in regras_extraidas:
                    elemento.is_core = (regras_extraidas['core'] == '+')
                    
                if 'permissivo' in regras_extraidas:
                    elemento.is_permissive = (regras_extraidas['permissivo'] == '+')

                #Caso uma prioridade ja seja encontrada define ela como a padrão
                if 'prioridade' in regras_extraidas:
                    elemento.prioridade = int(regras_extraidas['prioridade'])
                    
                print(f"[Interpretador] Elemento '{nome_codigo}' atualizado com sucesso.") #debug -> CLEAR retirar dps
            else:
                print(f"[Interpretador Aviso] O elemento '{nome_codigo}' existe no código do robô, mas não foi encontrado no arquivo de configuração.") #debug -> CLEAR retirar dps

        return variaveis_internas
    

## --------------> AGENTE CENTRAL - Ele avalia cada elemento da lista. Caso suas condições retornem true ele o adiciona na lista, caso ele seja o de maior prioridade, ele executa sua ação. Caso o elemento seja congelante ele apenas ignora as condições e executa sua ação. Caso um elemento core queira entrar na lista ele interrompe o elemento em execução e retoma o processo de avaliação da lista.
class AgenteCentral:
    def __init__(self, registro_elementos):
        self.elementos = registro_elementos
        self.elemento_congelante = None

    def avaliar(self, blackboard):
        vencedor = None
        maior_prio = -9999

        for element in self.elementos:
            if element.condicao(blackboard):
                
                if self.elemento_congelante is not None:
                    if not element.is_core:
                        continue
                    self.elemento_congelante = None

                if element.prioridade > maior_prio:
                    maior_prio = element.prioridade
                    vencedor = element

        if vencedor and vencedor.is_permissive:
            self.elemento_congelante = vencedor

        return vencedor.acao(blackboard) if vencedor else "idle"
    
    ## ---------------------------------- FUNÇÕES DE GERENCIAMENTO DE ELEMENTOS ----------------- ----------------------------------- ##
    #Tudo aqui é mais por teste, essas funções, no nivel atual dos elemento, não fazem sentido serem usadas. Um dos poucos casos que vejo sentido seria o uso deles em multiplos robos, onde um elemento de um robo pode ser adicionado ou removido do agente central de outro robo.

    #Adiciona um elemento
    def add_elemento(self, elemento):

        if self.elemento_congelante is not None:
            self.elementos.append(elemento)

    #Remove um elemento
    def remove_elemento(self, elemento):

        if not elemento.is_core:
            self.elementos.remove(elemento)

    #Limpa a lista
    def clear_elementos(self):

        for elemento in self.elementos:
            if not elemento.is_core:
                self.elementos.remove(elemento)
        
    #Adiciona um elemento DE FORMA FORÇADA
    def remove_elemento_admin(self, elemento):
        self.elementos.remove(elemento)
    
    #Remove um elemento DE FORMA FORÇADA
    def add_elemento_admin(self, elemento):
        self.elementos.append(elemento)

    #Limpa a lista DE FORMA FORÇADA
    def clear_elementos_admin(self):
        self.elementos.clear()

    #Adiciona um elemento e ja o executa
    def add_and_exec_elemento(self, elemento, blackboard):

        #Verifico se existe um elemento core na lista, caso sim, eu reavalio a lista. Caso contrário, eu adiciono o elemento modificando para que ele seja o de maior prioridade e reavalio a lista.

        exist_core = False

        for elem in self.elementos:
            if elem.is_core:
                exist_core = True
                break

        if exist_core:
            return self.avaliar(blackboard)
        
        new_elemento = elemento
        new_elemento.prioridade = max([elem.prioridade for elem in self.elementos]) + 1

        self.add_elemento(new_elemento)
        return self.avaliar(blackboard)
    
    #Adiciona um elemento e ja o executa de FORMA FORÇADA
    def add_and_exec_elemento(self, elemento, blackboard):

        #Eu adiciono o elemento modificando para que ele seja o de maior prioridade e reavalio a lista.
        new_elemento = elemento
        new_elemento.prioridade = max([elem.prioridade for elem in self.elementos]) + 1

        self.add_elemento(new_elemento)
        return self.avaliar(blackboard)
    

    

