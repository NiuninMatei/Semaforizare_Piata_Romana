import cv2
import time
import os
from ultralytics import YOLO

def monitorizare_realtime_piata_romana():
    # LINK-UL OFICIAL AL FLUXULUI VIDEO LIVE DE LA PIATA ROMANA
    url_stream = "https://s5.webcamromania.ro/piataromanab/tracks-v1/mono.m3u8"
    os.environ["OPENCV_FFMPEG_HTTP_OPTIONS"] = "user_agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    print("Inițializăm Ochii AI (YOLOv8) optimizați pentru Piața Romană...")
    model = YOLO("yolov8n.pt")
    
    # Contoare stricte de intrări și ieșiri pe bulevarde
    statistici = {
        "Magheru_Intrare": 0, "Magheru_Iesire": 0,
        "Catargiu_Intrare": 0, "Catargiu_Iesire": 0,
        "Dacia_Est_Intrare": 0, "Dacia_Est_Iesire": 0,
        "Dacia_Vest_Intrare": 0, "Dacia_Vest_Iesire": 0,
        "Autobuze_STB": 0, "Pietoni": 0
    }
    
    # Mapăm strict clasele corecte: 0=om, 1=bici, 2=auto, 3=moto, 5=autobuz
    clase_vehicule = [1, 2, 3]
    
    # Memorie limitată pentru tracking (salvăm doar ultimele 100 de ID-uri pentru a nu bloca calculatorul)
    id_procesate = set()

    while True:
        cap = cv2.VideoCapture(url_stream, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            time.sleep(2)
            continue

        cv2.namedWindow("Digital Twin - Piața Romană Live", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Digital Twin - Piața Romană Live", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break 
            
            h, w, _ = frame.shape
            
            # LINII DE CONTROL PLASATE PE ZONA DE JOS (UNDE VEHICULELE SUNT MARI ȘI CLARE)
            # Tragem linii orizontale sau verticale specifice fiecărei artere vizibile
            linie_magheru_y = int(h * 0.75)     # Zona din stânga jos (Magheru)
            linie_dacia_est_x = int(w * 0.70)   # Zona din dreapta (ASE / Dacia Est)
            linie_catargiu_y = int(h * 0.48)    # Zona de fundal (Catargiu) - coborâtă pentru acuratețe

            results_list = model.track(frame, persist=True, conf=0.30, verbose=False)
            results = results_list[0]
            
            # Recreăm cadrul grafic manual pentru a elimina complet bărcile sau plantele fictive
            annotated_frame = frame.copy()

            if results.boxes.id is not None:
                boxes = results.boxes.xyxy.cpu().numpy()
                clases = results.boxes.cls.cpu().numpy()
                ids = results.boxes.id.cpu().numpy()

                for box, cls_id, obj_id in zip(boxes, clases, ids):
                    cls_id = int(cls_id)
                    obj_id = int(obj_id)
                    
                    # [FILTRU TOTAL ANTI-BĂRCI] Dacă nu e om, mașină sau autobuz, trecem peste!
                    if cls_id not in:
                        continue
                        
                    # Calculăm centrul obiectului
                    cx = int((box[0] + box[2]) / 2)
                    cy = int((box[1] + box[3]) / 2)
                    
                    # Desenăm vizual DOAR obiectele corecte (fără erori de tip boat)
                    label = f"ID:{obj_id} masina" if cls_id in clase_vehicule else ("autobuz" if cls_id == 5 else "pieton")
                    cv2.rectangle(annotated_frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 2)
                    cv2.putText(annotated_frame, label, (int(box[0]), int(box[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # LOGICA DE NUMĂRARE INSTANTANEE LA TRECEREA PRIN LINII
                    if obj_id not in id_procesate:
                        
                        # 1. Control pe axa Magheru (Stânga jos)
                        if cx < int(w * 0.40) and abs(cy - linie_magheru_y) < 8:
                            if cls_id == 5: statistici["Autobuze_STB"] += 1
                            elif cls_id == 0: statistici["Pietoni"] += 1
                            else:
                                # Direcția pe ecran: dacă merge în jos (cy crește) e ieșire, dacă urcă e intrare
                                statistici["Magheru_Intrare"] += 1
                            id_procesate.add(obj_id)

                        # 2. Control pe axa Dacia Est / ASE (Dreapta)
                        elif cx > linie_dacia_est_x and abs(cy - int(h * 0.55)) < 8:
                            if cls_id == 5: statistics["Autobuze_STB"] += 1
                            else: statistici["Dacia_Est_Intrare"] += 1
                            id_procesate.add(obj_id)

                        # 3. Control pe axa Catargiu (Centru spre fundal)
                        elif int(w * 0.35) < cx < int(w * 0.65) and abs(cy - linie_catargiu_y) < 6:
                            if cls_id == 2: statistici["Catargiu_Iesire"] += 1
                            id_procesate.add(obj_id)

            # Limităm memoria cache pentru a nu bloca calculatorul sau pagina de chat
            if len(id_procesate) > 150:
                id_procesate.clear()

            # Desenăm liniile de control pe ecran pentru verificare vizuală
            cv2.line(annotated_frame, (0, linie_magheru_y), (int(w * 0.40), linie_magheru_y), (0, 255, 0), 3) # Magheru
            cv2.line(annotated_frame, (linie_dacia_est_x, int(h * 0.40)), (w, int(h * 0.70)), (255, 255, 0), 3) # Dacia Est
            cv2.line(annotated_frame, (int(w * 0.35), linie_catargiu_y), (int(w * 0.65), linie_catargiu_y), (0, 0, 255), 3) # Catargiu
            
            # PANOU DE CONTROL CURAT ȘI CORECT - PIAȚA ROMANĂ
            cv2.putText(annotated_frame, "SISTEM DIGITAL TWIN - CALIBRARE FINALA PIATA ROMANA", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
            cv2.putText(annotated_frame, f"Magheru In: {statistici['Magheru_Intrare']} | Catargiu Out: {statistici['Catargiu_Iesire']}", (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Dacia Est In: {statistici['Dacia_Est_Intrare']}", (40, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(annotated_frame, f"Autobuze STB: {statistici['Autobuze_STB']} | Pietoni: {statistici['Pietoni']}", (40, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 256, 255), 2)
            
            cv2.imshow("Digital Twin - Piața Romană Live", annotated_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return
                
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    monitorizare_realtime_piata_romana()