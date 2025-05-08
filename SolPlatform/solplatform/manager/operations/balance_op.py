import XPR_balance
import logging
import time 
import numpy as np 
class XPR_balance_op:
    """
    Include the operations of METTLER TOLEDO balance XPR204.
    Operations:
        open door(normally left), dispense solid
    """
    def __init__(self, 
                 balance: XPR_balance.XPR204,
                 logger: logging.Logger = None):
        """
        initialize the balance_operation
        Args:
            balance: a XPR204 object that is responsible for the communication with the balance 
            logger: logger
        """
        # initialize the xpr_balance
        self.balance = balance
        self.logger = logger
        # zero the balance once initialized
        try:
            self.balance.wakeup()
        except:
            pass
        self.balance.close_door()
        self.balance.zero()
        self.balance.close_door()
        
    def open_door(self, left: bool = True, right: bool = False):
        """
        wake up the balance and open the door 
        Args:
            left: choose open the left door of balance or not, normally not
            right: choose open the right door of balance or not, normally open
        """
        try:
            # ensure the balance is ready
            self.balance.wakeup()
        except:
            self.balance = XPR_balance.XPR204('192.168.1.17:81', logger = self.logger)
            self.balance.wakeup()
        # open the door, normally right door
        try:
            # ensure the balance is ready
            self.balance.open_door(left, right)
        except:
            self.balance = XPR_balance.XPR204('192.168.1.17:81', logger = self.logger)
            self.balance.open_door(left, right)
       

    def dispense(self, substance_name: str, amount: float, tolerance: int, task_name: str = "DOSING"):
        """
        perform a dispensing task and return the results
        Args:
            substance_name: the substance in the current dosing head
            amount: the amount of solid powder wanted to add in mg
            tolerance: the tolerance of adding solid powder, normally 0-100
        """
        try:
            # ensure the balance is ready
            self.balance.wakeup()
        except:
            pass
        amount = np.around(amount)
        # add solid and record the weighing data
        data = self.balance.dispense(substance_name, amount, tolerance, task_name)

        # return weighing data
        return data
        
        