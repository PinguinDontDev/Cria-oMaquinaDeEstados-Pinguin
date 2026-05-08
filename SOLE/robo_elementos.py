
from framework_base import BlackboardBase, ElementoBase, registrar_elemento

class RoboBlackboard(BlackboardBase):
    def __init__(self):
        self.fall_state = 'Up'
        self.ball_found = False
        self.ball_close = False
        self.hor_motor_out_of_center = 'Center'
        self.head_kick_check = False
        self.kick_done = False
        self.win = False

@registrar_elemento
class ElementoLevantar(ElementoBase):
    def __init__(self):
        super().__init__("Levantar")

    def condicao(self, bb):
        return bb.fall_state != 'Up'

    def acao(self, bb):
        return "getting_up"

@registrar_elemento
class ElementoProcurar(ElementoBase):
    def __init__(self):
        super().__init__("Procurar")

    def condicao(self, bb):
        return not bb.ball_found and bb.fall_state == 'Up'

    def acao(self, bb):
        return "searching"

@registrar_elemento
class ElementoChutar(ElementoBase):
    def __init__(self):
        super().__init__("Chutar")

    def condicao(self, bb):
        return (bb.head_kick_check and 
                bb.ball_close and 
                bb.hor_motor_out_of_center == 'Center' and 
                bb.fall_state == 'Up' and 
                not bb.kick_done)

    def acao(self, bb):
        return "kicking"
    
@registrar_elemento
class ElementoWin(ElementoBase):
    def __init__(self):
        super().__init__("Win")

    def condicao(self, bb):
        return (bb.win)

    def acao(self, bb):
        return "Win"