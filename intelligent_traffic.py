import os
import sys
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import traci

# Configurare mediu SUMO
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Eroare: Setează variabila de mediu 'SUMO_HOME'")

class PiațaRomanăTrafficEnv(gym.Env):
    """Mediu custom Gymnasium pentru optimizarea semaforizării din Piața Romană"""
    metadata = {"render_modes": ["human"]}

    def __init__(self, config_file="osm.sumocfg"):
        super(PiațaRomanăTrafficEnv, self).__init__()
        self.config_file = config_file
        self.id_semafor = "joinedS_2404247020_2404247023_3262378104_6271858398_#5more"
        
        # Definim fazele verzi principale din Piața Romană (extrase din scanarea ta anterioară)
        # Am selectat fazele majore de verde: 0, 3, 6, 9, 12, 15, 18, 21, 24, 27
        self.macro_faze = [0, 3, 6, 9, 12, 15, 18, 21, 24, 27]
        
        # Spațiul de acțiuni: AI-ul alege una dintre cele 10 faze verzi
        self.action_space = spaces.Discrete(len(self.macro_faze))
        
        # Spațiul de stări: AI-ul observă lungimea cozilor pe 5 zone critice
        self.observation_space = spaces.Box(low=0, high=500, shape=(5,), dtype=np.float32)
        
        self.sumo_pornit = False

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        if self.sumo_pornit:
            traci.close()
            self.sumo_pornit = False
            
        # Pornim SUMO în mod accelerat fără interfață grafică pentru antrenare rapidă
        traci.start(["sumo", "-c", self.config_file, "--start", "--quit-on-end"])
        self.sumo_pornit = True
        
        state = self._get_state()
        info = {}
        return state, info

    def _get_state(self):
        """AI-ul citește numărul de vehicule blocate pe arterele din Piața Romană"""
        try:
            # Luăm lista de benzi controlate de semaforul din Romană (funcția corectată!)
            benzi_controlate = traci.trafficlight.getControlledLanes(self.id_semafor)
        except traci.exceptions.TraCIException:
            benzi_controlate = []

        cozi = [0, 0, 0, 0, 0]
        
        # Monitorizăm vehiculele care au viteza aproape de zero (stau la coadă)
        # Împărțim datele brute din intersecție în 5 vectori de stare pentru rețeaua neuronală
        vehicule = traci.vehicle.getIDList()
        for veh_id in vehicule:
            try:
                if traci.vehicle.getSpeed(veh_id) < 0.1:
                    lane_id = traci.vehicle.getLaneID(veh_id)
                    if lane_id in benzi_controlate:
                        # Împărțim simbolic cozile pe cele 5 brațe ale intersecției
                        idx = hash(lane_id) % 5
                        cozi[idx] += 1
            except traci.exceptions.TraCIException:
                continue
            
        state = np.array(cozi, dtype=np.float32)
        return state

    def step(self, action):
        # AI-ul aplică faza de verde aleasă
        faza_sumo = self.macro_faze[action]
        traci.trafficlight.setPhase(self.id_semafor, faza_sumo)
        
        timp_asteptare_inainte = self._get_total_waiting_time()
        
        # AI-ul lasă timpul să curgă 10 secunde în simulator sub această fază verde
        for _ in range(10):
            if traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                
        timp_asteptare_dupa = self._get_total_waiting_time()
        
        state = self._get_state()
        
        # Recompensa: Penalizăm dacă timpul total de așteptare în secundă a crescut
        # AI-ul va dori să scadă timpul total de așteptare (reward pozitiv sau cât mai mic negativ)
        reward = float(-(timp_asteptare_dupa - timp_asteptare_inainte))
        
        terminated = traci.simulation.getMinExpectedNumber() == 0
        truncated = False
        info = {}
        
        return state, reward, terminated, truncated, info

    def _get_total_waiting_time(self):
        """Calculează secundele totale de așteptare ale tuturor vehiculelor de pe hartă"""
        total_time = 0
        for veh_id in traci.vehicle.getIDList():
            try:
                total_time += traci.vehicle.getWaitingTime(veh_id)
            except traci.exceptions.TraCIException:
                continue
        return total_time

    def close(self):
        if self.sumo_pornit:
            traci.close()
            self.sumo_pornit = False

# --- SECȚIUNEA DE ANTRENARE A INTELIGENȚEI ARTIFICIALE ---
if __name__ == "__main__":
    from stable_baselines3 import PPO
    
    print("Inițializăm mediul digital al Pieței Romane...")
    env = PiațaRomanăTrafficEnv()
    
    print("Construim Rețeaua Neuronală de tip PPO (Proximal Policy Optimization)...")
    model = PPO("MlpPolicy", env, verbose=1, learning_rate=0.0003, n_steps=64)
    
    print("Pornim procesul de antrenare a AI-ului...")
    # Antrenăm modelul pentru 2000 de pași de intersecție
    model.learn(total_timesteps=2000)
    
    # Salvăm creierul AI antrenat
    model.save("ai_semafor_romana")
    print("\n[SUCCES] Antrenare finalizată! Modelul 'ai_semafor_romana.zip' a fost salvat.")
    
    env.close()