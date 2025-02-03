# Utiliser l'image de base Gitpod (par exemple, workspace-full qui contient déjà de nombreux outils)
FROM gitpod/workspace-full

# Mettre à jour et installer les paquets nécessaires
RUN sudo apt-get update && \
    sudo apt-get install -y python3-tk xvfb fluxbox x11vnc novnc

# Copier votre code dans le conteneur (optionnel si vous travaillez directement depuis le dépôt)
COPY . /workspace

# Exposer un port pour le VNC (novnc utilise généralement le port 6080)
EXPOSE 6080

# Définir le point d'entrée pour lancer le gestionnaire de fenêtres, le serveur VNC et votre application.
# Ici, on crée un script de démarrage pour lancer fluxbox, x11vnc et xvfb-run avec votre code.
CMD bash -c "\
  fluxbox & \
  x11vnc -display :0 -forever -nopw -listen 0.0.0.0 -xkb & \
  xvfb-run -a -s '-screen 0 1024x768x24' python3 main.py"
