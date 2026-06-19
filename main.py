#!/usr/bin/env python3
#coding=utf-8
'''
Verificar a adição do game controller e funcionamento no ros2
'''

import time
from modularized_bhv_msgs.msg import CurrentStateMsg

CENTER = 'Center'
LEFT = 'Left'
RIGHT = 'Right'
UP = 'Up'

class StateMachine:

    def __init__(self):
        """
        Construtor da máquina de estados (Refatorada para Utility AI via Lista)
        """
        self.state = 'idle_march'

        # Variáveis nativas do código original para tempo de estabilização
        self.enter_time = None
        self.march_duration = 1.0
        self.idle_duration = 1.5

        # flags internas (privadas)
        self._walking_condition = False
        self._getting_up_condition = False
        self._kick_condition = False
        self._kick_done_condition = False
        self._aligning_condition = False    
        self._search_condition = False
        self._impossible_condition = False

        self.state_msg = CurrentStateMsg()

    def request_state_machine_update(self, ball_position, ball_close, ball_found, fall_state, 
                                     hor_motor_out_of_center, head_kick_check, kick_done):
        """
        Atualiza as condições da máquina de estados e retorna o estado atual
        """
        # Atualiza flags de condição originais
        self.search_condition_update(ball_found)
        self.getting_up_condition_update(fall_state)
        self.walking_condition_update(ball_found, ball_close)
        self.kick_condition_update(head_kick_check, ball_close, hor_motor_out_of_center)
        self.kick_done_condition_update(kick_done)
        self.aligning_condition_update(hor_motor_out_of_center)

        self.update_state()
        
        print(f'-------------------\nEstado {self.state}')        
        self.state_msg.current_state = str(self.state)
        return self.state_msg
    
    def update_state(self):
        """
        Avalia todas as condições através da lista de controle.
        O estado com maior prioridade decide a ação atual.
        """
        control_list = []
        
        #prioridades
        class PRIORITY:
            GETTING_UP = 100
            KICK_IN_PROGRESS = 95  
            SEARCHING = 90
            STABILIZATION = 85
            KICKING = 75           
            ALIGNING = 65
            WALKING = 60
            POST_GETTING_UP = 40

        #dicionarios
        kick_prerequisites = {
            'aligning': ('idle', PRIORITY.STABILIZATION),
            'idle_march': ('idle', PRIORITY.STABILIZATION),
            'walking': ('idle_march', PRIORITY.STABILIZATION)
        }

        aligning_prerequisites = {
            'walking': ('idle_march', PRIORITY.STABILIZATION),
            'idle_march': ('aligning', PRIORITY.ALIGNING)
        }


        # Adicionando a lista a condição de levantar
        if self._getting_up_condition:
            control_list.append(('getting_up', PRIORITY.GETTING_UP))

        # Trava de estado: se está executando o chute (kick_done == True indica processo de chute),
        # deve continuar no estado 'kicking' com prioridade altíssima.
        if self._kick_done_condition:
            control_list.append(('kicking', PRIORITY.KICK_IN_PROGRESS))

        # Adicionando a lista a condição de procurar a bola
        if self._search_condition:
            control_list.append(('searching', PRIORITY.SEARCHING))

        # Estabilização - a mesma coisa do codigo original, mas com o sistema de prioridade de lista.
        # Mantemos o robô estabilizando dando uma prioridade alta temporária ao estado atual
        if self.state == 'idle_march':
            if self.enter_time is None:
                self.enter_time = time.time()
            if (time.time() - self.enter_time) < self.march_duration:
                control_list.append(('idle_march', PRIORITY.STABILIZATION))
            else:
                self.enter_time = None  # Tempo acabou, a "trava" some da lista

        elif self.state == 'idle':
            if self.enter_time is None:
                self.enter_time = time.time()
            if (time.time() - self.enter_time) < self.idle_duration:
                control_list.append(('idle', PRIORITY.STABILIZATION))
            else:
                self.enter_time = None

        # Vendo se o robo está pronto para chutar, se não, ele vai para o estado de estabilização, 
        # exigindo pré-chute ou pré-alinhamento dependendo do estado atual, caso contrário, ele vai para o estado de chute.
        if self._kick_condition:
            control_list.append(kick_prerequisites.get(self.state, ('kicking', PRIORITY.KICKING)))

        # Vendo se o robo precisa se alinhar, se não, ele vai para o estado de estabilização, 
        # exigindo pré-alinhamento dependendo do estado atual, caso contrário, ele vai para o estado de alinhamento.
        if self._aligning_condition:
            control_list.append(aligning_prerequisites.get(self.state, ('aligning', PRIORITY.ALIGNING)))

        # Andando :D
        if self._walking_condition:
            control_list.append(('walking', PRIORITY.WALKING))

        # Caso eu caia, adicone a condição de levantar a lista
        if self.state == 'getting_up' and not self._getting_up_condition:
            control_list.append(('idle_march', PRIORITY.POST_GETTING_UP))

        # Quak a chance de tudo da errado e nenhum estado ser selecionado? Por via das duvida, aqui a segurança
        if len(control_list) == 0:
            control_list.append((self.state, 0))


        # SELECIONANDO MAIOR PRIORIDADE DA LISTA
        max_val = -9999
        novo_estado = self.state

        for estado, prioridade in control_list:
            if prioridade > max_val:
                max_val = prioridade
                novo_estado = estado

        
        # Debug e reset do relogio
        if novo_estado != self.state:
            print(f'Transição feita: {self.state} -> {novo_estado}')
            self.state = novo_estado

            if self.state not in ['idle_march', 'idle']:
                self.enter_time = None


    # ----- FUNÇÕES UPDATE CONDITION -----
    def search_condition_update(self, ball_found):
        self._search_condition = not ball_found

    def getting_up_condition_update(self, fall_state):
        self._getting_up_condition = (fall_state != UP)

    def kick_done_condition_update(self, kick_done):
        self._kick_done_condition = kick_done

    def walking_condition_update(self, ball_found, ball_close):
        self._walking_condition = (ball_found and not ball_close)

    def kick_condition_update(self, head_kick_check, ball_close, hor_motor_out_of_center):
        self._kick_condition = (head_kick_check and ball_close and hor_motor_out_of_center == CENTER)

    def aligning_condition_update(self, hor_motor_out_of_center):
        self._aligning_condition = (hor_motor_out_of_center != CENTER) 

    # ----- FUNÇÕES RETURN CONDITION-----
    def search_condition(self): 
        return self._search_condition

    def walking_condition(self): 
        return self._walking_condition  
    
    def getting_up_condition(self): 
        return self._getting_up_condition  
    
    def kick_condition(self):
        return self._kick_condition
    
    def kick_done_condition(self):
        return self._kick_done_condition    
    
    def aligning_condition(self): 
        return self._aligning_condition
    
    def impossible_condition(self): 
        return self._impossible_condition