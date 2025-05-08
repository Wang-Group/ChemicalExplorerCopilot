import smtplib
import yaml
import os
import logging
import numpy as np
import threading
import random
import matplotlib.pyplot as plt
from email.mime.text import MIMEText
from email.utils import formataddr
from copy import copy
from typing import Union, Optional
from scipy.stats import norm, uniform
from scipy.optimize import fsolve



def add_lock(device):
    """
    add lock for the device which does not hava a lock.

    Args:
        device: _description_
    """
    if not hasattr(device, "lock"):
        device.lock = threading.Lock()
        return True
    else:
        return True

def aquire(device):
    """
    Aquire the lock object in the selected device.

    Args:
        device: the device which has a lock object

    """
    if device.lock:
        device.lock.acquire()
    else: 
        raise SyntaxError("there is no lock in the class")

def release(device):
    """
    Aquire the lock object in the selected device.

    Args:
        device: the device which has a lock object
    """
    if device.lock:
        device.lock.release()
    else: 
        raise SyntaxError("there is no lock in the class")

def check_obj_status(obj: str, plate: Optional[str] = None, idx: Optional[int] = None, mapping: Optional[dict] = None):
    """
    check if there is any obj on target holder. if so, return its name. else, return False
    Args:
        obj_type: the type of object, e.g.: 'vial', 'cap', 'head', 'tip'
        idx: the position of holder wanted to check
    Return:
        if the item is on the holder or not. if the item is on the holder, return the name of the item. 
    """
    if obj == 'vial':
        for bottle in mapping['Vials']:
            if mapping['Vials'][bottle]["bottle_plate"] == plate and mapping['Vials'][bottle]["slot_index"] == idx:
                return bottle
        return False
    elif obj == 'head':
        for head in mapping['Heads']:
            if mapping['Heads'][head]["head_plates"] == plate and mapping['Heads'][head]["slot_index"] == idx:
                return head
        return False
    elif obj == 'cap':
        for cap in mapping['Caps']:
            if mapping['Caps'][cap]["cap_plate"] == plate and mapping['Caps'][cap]["slot_index"] == idx:
                return cap
        return False
    elif obj == 'funnel':
        for funnel in mapping["Funnels"]:
            if not mapping['Funnels'][funnel]["solid"]:
                return funnel
    elif obj == 'tip':
        for tip in mapping["Tips"]:
            if mapping["Tips"][tip] == idx:
                return tip
    elif obj == 'feeder':
        for feeder in mapping["Feeders"]:
            if mapping["Feeders"][feeder] == plate:
                return feeder
        return False
    else: 
        raise ValueError(f"obj can only be vial, head or cap, current value is {obj}")

def exp_name_from_file_path(file_path: str):
    """
    Get the file_name from the file path.

    Args:
        file_path: the path of the file.

    """
    base_name = os.path.basename(file_path)
    file_name = os.path.splitext(base_name)[0]
    return file_name

class MailSender:
    """
    Send e-mail to target mail address.
    """

    def __init__(self, mail_config_path: str, logger: logging.Logger) -> None:
        """
        initialize the infomation of sender and receiver from the import config file.

        Args:
            mail_config_path: the path of the mail config path
            logger: logger
        """
        # load the config message
        with open(mail_config_path, "r", encoding="utf-8") as mail_config: 
            self.mail_config = yaml.safe_load(mail_config)
        self.user_account = self.mail_config["user_account"]
        self.password = self.mail_config["password"]
        self.receiver_account = tuple(self.mail_config["receiver_account"])
        self.smtp_server = self.mail_config["smtp_server"]
        self.nickname = self.mail_config["nickname"]
        self.logger = logger
    
    def send_message(self, subject: str, msg: str):
        """
        Open the mail account and send message with subject and the text, then close.

        Args:
            subject: the mail subject.
            msg: the text of the mail.
        """
        # format the message of the mail
        message = MIMEText(msg, "plain", "utf-8")
        message["From"] = formataddr(
            [self.nickname, self.user_account]
        )
        message["To"] = ", ".join(self.receiver_account)
        message["Subject"] = subject
        # create the mail service, send the formatted message, close the service.
        try:    
            with smtplib.SMTP_SSL(self.smtp_server[0], self.smtp_server[1]) as server:
                server.login(self.user_account, self.password)
                server.sendmail(self.user_account, 
                                self.receiver_account, 
                                message.as_string())
                server.quit()
            self.logger.info("email sent success")
            print("email sent success")
        except Exception as e:
            self.logger.warning(f"email sent failed: {e}")
            print(f"email sent failed: {e}")

reagents = {
            'dilute_acid': 0.1, 
            'dilute_base': 0.1,
        }
class PHAdjustmentEnv:
    def __init__(self):
        
        self.steps_taken = 0
        self.done = False

        self.total_volume = 11.02  
        self.previous_total_volume = 11.02 # origin solution volume，mL
        self.acid_added = 0.0      # acid，mol
        self.base_added = 0.0      # base，mol
        self.last_acid_added = 0.0
        self.last_base_added = 0.0

        # define the concentration of reagent：mol/L
        self.reagents = reagents

        # min addition volume, mL（100 uL）
        self.min_addition_volume = 0.1

        # volume list, max to 1 mL
        self.addition_volumes = [self.min_addition_volume * i for i in range(1, 11)]  # max addition: 1 mL

        # action space
        self.action_space = []
        for reagent in self.reagents.keys():
            for volume in self.addition_volumes:
                self.action_space.append((reagent, volume))
        

    def _initialize_env(self, 
                        init_pH, 
                        target_pH, 
                        max_steps, 
                        num_buffers = 2, 
                        pKa_range = (2.0, 6.0), 
                        conc_range = (0.000001, 0.015)):
        
        self.initial_ph = init_pH
        self.current_ph = init_pH
        self.previous_ph = init_pH
        self.target_ph = target_pH
        self.num_buffers = num_buffers
        self.pKa_list = np.random.uniform(pKa_range[0], pKa_range[1], size=self.num_buffers)
        self.buffer_conc = np.random.uniform(conc_range[0], conc_range[1], size=self.num_buffers)
        self.max_steps = max_steps
        # Initialize prior distribution (uniform distribution)
        self.priors = []
        for i in range(self.num_buffers):
            pKa_prior = uniform(loc=self.pKa_list[i], scale=pKa_range[1] - pKa_range[0])
            conc_prior = uniform(loc=self.buffer_conc[i], scale=conc_range[1] - conc_range[0])
            self.priors.append({'pKa': pKa_prior, 'conc': conc_prior})
        self.update_intial_state()

    def update_intial_state(self):
        H_conc = 10 ** (-self.current_ph)
        self.acid_added = 0
        # The [A-] concentration of each buffer pair was calculated and accumulated to the total concentration of the added base
        for i in range(self.num_buffers):
            Ka = 10 ** (-self.pKa_list[i])
            total = self.buffer_conc[i] # Adjust the concentration to account for changes in solution volume
            A_minus = total * Ka / (Ka + H_conc)
            self.base_added += A_minus * (self.total_volume / 1000) # [A-]
        # self.priors = self.initialize_prior()
        
    def charge_balance(self, H_conc):
        if H_conc <= 0:
            return np.inf

        OH_conc = 1e-14 / H_conc
        # Total positive ion concentration: [H+] + [Na+] + [K+]
        positive_charge = H_conc + self.base_added / (self.total_volume / 1000)  # mol/L
        # Total negative ion concentration：[OH-] + [Cl-] + [NO3-] + sum([A-])
        negative_charge = OH_conc + self.acid_added / (self.total_volume / 1000)  # mol/L

        # Calculate [A-] concentration for each buffer pair and accumulate to total negative ion concentration
        for i in range(self.num_buffers):
            Ka = 10 ** (-self.pKa_list[i])
            # Adjust concentration to account for changes in solution volume
            total = self.buffer_conc[i] * self.previous_total_volume / self.total_volume
            # Fix me:
            A_minus = total * Ka / (Ka + H_conc) 
            negative_charge += A_minus  # [A-] 
        # Return charge balance difference
        return positive_charge - negative_charge

    def update_cal_ph(self):
        """
        Calculate the pH expected with the addition of acid and base in the absence of buffering.
        """
        # Change in total volume
        V_prev = self.previous_total_volume  # Volume before addition, mL
        V_total = self.total_volume          # Volume after addition, mL
        # H+ concentration before addition
        H_prev = 10 ** (-self.previous_ph)  # mol/L
        # Total H+ before addition
        n_H_prev = H_prev * (V_prev / 1000)  # mol
        # Amount of acid and base added for this operation (mol)
        delta_n_H = self.last_acid_added - self.last_base_added  # Positive values acids, negative values bases
        # Total H+ after addition (assuming no buffer)
        n_H_after = n_H_prev + delta_n_H
        # Calculate H+ concentration without buffer
        if n_H_after > 0:
            H_no_buffer = n_H_after / (V_total / 1000) 
            print("hello", H_no_buffer) # mol/L
        elif n_H_after == 0:
            H_no_buffer = 1e-7  # Neutral solution
        else:
            # If the net addition of base is excessive, calculate the corresponding OH- concentration and convert to H+ concentration.
            n_OH_after = -n_H_after  # mol
            OH_conc = n_OH_after / (V_total / 1000)  # mol/L
            H_no_buffer = 1e-14 / OH_conc  # mol/L
        # Calculate pH without buffer
        pH_no_buffer = -np.log10(H_no_buffer)
        # Generate 3 initial guesses between previous_ph and pH_no_buffer on the pH scale
        pH_values = [self.previous_ph]
        for i in range(1, 4):
            fraction = i / 4.0
            pH_guess = self.previous_ph + fraction * (pH_no_buffer - self.previous_ph)
            pH_values.append(pH_guess)
        pH_values.append(pH_no_buffer)
        # Convert pH to H+ concentration as a list of initial guesses
        initial_guesses = [10 ** (-pH) for pH in pH_values]
        best_H_conc = None
        best_residual = None
        for H_guess in initial_guesses:
            try:
                H_solution = fsolve(self.charge_balance, H_guess, xtol=1e-12)
                H_conc = H_solution[0]
                if H_conc > 0:
                    residual = abs(self.charge_balance(H_conc))
                    if best_residual is None or residual < best_residual:
                        best_H_conc = H_conc
                        best_residual = residual
            except:
                continue

        if best_H_conc and best_H_conc > 0:
            self.current_ph = -np.log10(best_H_conc)
        else:
            self.current_ph = np.nan

    def update_exp_ph(self,pH):

        self.current_ph = pH

    def step(self, action, cal_or_exp,pH):
        if self.done:
            raise Exception("Episode is done")
        # Unpacking actions
        reagent, volume = action  
        added_moles = self.reagents[reagent] * (volume / 1000)  # mol
        # Preserve pH and total solution volume before addition
        self.previous_ph = self.current_ph
        self.previous_total_volume = self.total_volume  # mL
        # Total volume of updated solution
        self.total_volume += volume  # mL
        # Record the amount of acid and base added this time
        self.last_acid_added = 0.0
        self.last_base_added = 0.0
        # Update the amount of acid and alkali added
        if 'acid' in reagent:
            self.acid_added += added_moles
            self.last_acid_added = added_moles
        elif 'base' in reagent:
            self.base_added += added_moles
            self.last_base_added = added_moles
        # Update the current pH value
        if cal_or_exp == 'cal':
            self.update_cal_ph()
        else:
            self.update_exp_ph(pH)
        self.steps_taken += 1
        # Check if current_ph is a valid value
        if np.isnan(self.current_ph) or self.current_ph < 0 or self.current_ph > 14:
            reward = -100  # The Great Punishment
            self.done = True
            return self.current_ph, reward, self.done, {}

        # Calculation of incentives
        ph_error = abs(self.current_ph - self.target_ph)
        # The closer the pH is to the target, the higher the reward
        reward = -ph_error 
        # 20 seconds per measurement, cumulative time cost
        time_penalty = self.steps_taken * 20  # unit: s
        reward -= time_penalty * 0.01  # Weighting of time penalties
        # Determine if it's done
        if ph_error < 0.1 or self.steps_taken >= self.max_steps:
            self.done = True
        return self.current_ph, reward, self.done, {}

    def env_copy(self):
        env_copied = PHAdjustmentEnv()
        env_copied.buffer_conc = self.buffer_conc
        env_copied.acid_added = self.acid_added
        env_copied.base_added = self.base_added
        env_copied.current_ph = self.current_ph
        env_copied.target_ph = self.target_ph
        env_copied.last_acid_added = self.last_acid_added
        env_copied.last_base_added = self.last_base_added
        env_copied.previous_ph = self.previous_ph
        env_copied.total_volume = self.total_volume
        env_copied.previous_total_volume = self.previous_total_volume
        env_copied.num_buffers = self.num_buffers
        env_copied.pKa_list = self.pKa_list
        env_copied.max_steps = self.max_steps
        return env_copied
    
    def sample_parameters(self):
        sampled_pKa = []
        sampled_conc = []
        for prior in self.priors:
            pKa_sample = prior['pKa'].rvs()
            conc_sample = prior['conc'].rvs()
            sampled_pKa.append(pKa_sample)
            sampled_conc.append(conc_sample)
        return sampled_pKa, sampled_conc

    def select_best_action(self):
        best_action = None
        best_reward = -np.inf
        for action_index, action in enumerate(self.action_space):
            # Create a copy of the environment to avoid affecting the real environment
            # Copy the state of the current environment
            env_copied = self.env_copy()
            # execute an action
            next_ph, reward, done, _ = env_copied.step(action,'cal',0)
            # Calculate incentives (based on difference in distance from target pH)
            ph_error = abs(next_ph - self.target_ph)
            reward = -ph_error
            if reward > best_reward:
                best_reward = reward
                best_action = action
        return best_action, done

    def update_posteriors(self, action, observed_ph):
        # Using particle filtering
        num_particles = 1000
        particles = []
        weights = []
        for _ in range(num_particles):
            # Sampling parameters from a priori
            sampled_pKa, sampled_conc = self.sample_parameters()
            # Predicts the pH value after the action is performed under the sampled parameters.
            predicted_ph = self.predict_ph(action, sampled_pKa, sampled_conc)
            # Calculate the likelihood (assuming the measurement error follows a normal distribution)
            likelihood = norm.pdf(observed_ph, loc=predicted_ph, scale=0.1)
            # print(f"observed pH :{observed_ph} vs predicted pH: {predicted_ph}")
            particles.append((sampled_pKa, sampled_conc))
            weights.append(likelihood)
        # normalized weight
        weights = np.array(weights)
        weights += 1e-10  # Prevent division by zero
        weights /= np.sum(weights)
        # resample
        indices = np.random.choice(range(num_particles), size=num_particles, p=weights)
        new_priors = []
        for idx in indices:
            pKa_sampled, conc_sampled = particles[idx]
            # Updating the prior distribution to the resampled distribution
            for i in range(self.num_buffers):
                self.priors[i]['pKa'] = uniform(loc=pKa_sampled[i], scale=1e-5)  # narrow distribution
                self.priors[i]['conc'] = uniform(loc=conc_sampled[i], scale=1e-5)
            new_priors.append(self.priors)
        # Return the new prior distribution
        self.priors = new_priors[0]  # Because all priors are updated to the same distribution
        for i in range(len(self.priors)):
            self.pKa_list[i] = self.priors[i]['pKa'].mean() ####################
            self.buffer_conc[i] = self.priors[i]['conc'].mean() ################

    def predict_ph(self, action, sampled_pKa, sampled_conc):
        # Create a copy of the environment
        env_copy = self.env_copy()
        # Copying the state of the current environment
        # execute an action
        next_ph, _, _, _ = env_copy.step(action,'cal',0)
        return next_ph
    
    def suggest_next_action(self, action, observed_ph):
        # execute an action
        observed_ph, reward, done, _ = self.step(action, 'exp', observed_ph)
        print(f" Action = {action}, Observed pH = {observed_ph:.2f}, Reward = {reward:.2f}")
        if done:
            print("Reach target pH or maximum number of steps.")
        # Sampling parameters from the posterior distribution
        self.update_posteriors(action, observed_ph)
        # Selection of the optimal action based on the sampled parameters
        next_action, _done = self.select_best_action()
        print(next_action)
        return next_action, done