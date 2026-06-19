from framework_base import AgenteCentral, Interpretador, registro_global_elementos
from robo_elementos import RoboBlackboard

#Iniciando motor
Interpretador.carregar_e_aplicar_configuracoes('regras.slel')
bb = RoboBlackboard()
agente = AgenteCentral(registro_global_elementos)

def request_state_machine_update(ball_position, ball_close, ball_found, fall_state, 
                                 hor_motor_out_of_center, head_kick_check, kick_done):
    
    # Atualiza a mente do robô
    bb.ball_found = ball_found
    bb.ball_close = ball_close
    bb.fall_state = fall_state
    bb.hor_motor_out_of_center = hor_motor_out_of_center
    bb.head_kick_check = head_kick_check
    bb.kick_done = kick_done

    #motor funcionando
    estado_atual = agente.avaliar(bb)
    print(f'Estado Decidido: {estado_atual}')
    print('-------------------')
    return estado_atual

