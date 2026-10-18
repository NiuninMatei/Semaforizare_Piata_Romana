import os
import sys
import traci

# Verificăm dacă SUMO este instalat corect în sistem
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Eroare: Te rog să configurezi variabila de mediu 'SUMO_HOME'")

def ruleaza_simulare():
    """Funcția principală în care AI-ul va controla semafoarele pas cu pas"""
    # Deschidem conexiunea cu fișierul de configurare generat de WebWizard
    sumo_config = "osm.sumocfg"
    
    # Pornim SUMO cu interfață grafică (sumo-gui)
    traci.start(["sumo-gui", "-c", sumo_config, "--start"])
    
    print("Simularea a pornit! Conexiunea TraCI este activă.")
    
    pas = 0
    # Simularea rulează pas cu pas până când toate mașinile părăsesc harta
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()  # Avansează simularea cu o secundă
        
        # AICI va veni logica de Inteligență Artificială!
        # De exemplu, la fiecare 10 secunde putem citi cozile de la Piața Romană
        if pas % 10 == 0:
            print(f"Pasul {pas}: Monitorizăm traficul în Piața Romană...")
            
        pas += 1
        
    traci.close()
    print("Simularea s-a încheiat cu succes.")

if __name__ == "__main__":
    ruleaza_simulare()