# Bo7 Zombies Simple Tool

A small Windows app for the **Lumen offline client** of Black Ops 7 that types console commands into the game for you.
Una app para Windows para el **cliente offline Lumen** de Black Ops 7 que escribe los comandos de consola en el juego por vos.

**[English](#english) · [Español](#español)**

---

## English

### Features
- **Game modes:** Standard, Cursed, Directed, Mister Peeks Mayhem, Rogue Run, Training Course, Survival, Cursed Survival
- **One-click maps:** starts the private match for you (`xstartprivateparty` → lobby → `ui_mapname` → `setgametype` → `xpartygo`)
- **Survival maps:** Ashes (Farm, Exit 115, Cosmodrome, Ashwood), Astra Malorum (Mars), Paradox Junction (Nuked), Totenreich (Lighthouse), Kowakujō (Castle)
- **Relic step** for Cursed, Cursed Survival and Mister Peeks Mayhem (opens the relic menu and waits for you)
- **Easter eggs** enabled on every map, plus the **Rex Infernus super EE**
- **Rampage Inducer** enabled (except Directed, Rogue Run and Dead Ops Arcade)
- **Optional:** start with +100k essence, +25k salvage / rare salvage and all doors open (`zombie_cheat 3`)
- **Camos:** BO6 / MW2 / MW3 mastery, ranked, CDL, event and special camos
- **Wonder weapons:** Ray Gun, Ray Gun Mk II, Blundergat, Wunderwaffe DG-2 and more
- **Reset weapon** button to unbug your loadout
- **Leave match** button (`disconnect` + automatic ESC spam to fix the laggy menus)
- English / Español

### How to use
1. Open BO7 with Lumen and go to the **Zombies** menu.
2. Run **`Bo7 Zombies Simple Tool.exe`** (from Releases). It asks for admin rights; it needs them to send keys to the game.
3. Pick a mode, then a map. Don't touch the keyboard while it types.

### Notes
- Offline / Lumen only. Do not use online.
- Some antivirus software flags it. That's a false positive: it's a Python app (PyInstaller) that simulates key presses. The full source code is in this repo.
- Console key: the one above Tab. If the console doesn't open, change the method in **Settings**.

### Build from source
Requires Python 3 for Windows. Put `build_exe.bat` next to `Bo7 Zombies Simple Tool.pyw` and double-click it. The `.exe` is created in `dist/`.

---

## Español

### Funciones
- **Modos de juego:** Estándar, Maldito, Guiado, Mister Peeks Mayhem, Operación Rogue, Curso de entrenamiento, Sobrevivencia, Sobrevivencia Maldito
- **Mapas con un clic:** arranca la partida privada sola (`xstartprivateparty` → lobby → `ui_mapname` → `setgametype` → `xpartygo`)
- **Mapas de sobrevivencia:** Ashes (Granja, Salida 115, Cosmódromo, Ashwood), Astra Malorum (Marte), Paradox Junction (Nuked), Totenreich (Faro), Kowakujō (Castillo)
- **Paso de reliquias** para Maldito, Sobrevivencia Maldito y Mister Peeks Mayhem (abre el menú y espera a que confirmes)
- **Easter eggs** activados en todos los mapas, más el **super EE de Rex Infernus**
- **Inductor de velocidad** activado (menos en Guiado, Operación Rogue y Dead Ops Arcade)
- **Opcional:** empezar con +100k esencia, +25k chatarra / chatarra rara y puertas abiertas (`zombie_cheat 3`)
- **Camos:** maestrías de BO6 / MW2 / MW3, ranked, CDL, eventos y especiales
- **Armas maravilla:** Ray Gun, Ray Gun Mk II, Blundergat, Wunderwaffe DG-2 y más
- Botón **Reiniciar arma** para desbugear la clase
- Botón **Salir de la partida** (`disconnect` + ESC automático para arreglar los menús lentos)
- English / Español

### Cómo usarlo
1. Abrí BO7 con Lumen y andá al menú de **Zombies**.
2. Abrí **`Bo7 Zombies Simple Tool.exe`** (desde Releases). Pide administrador; lo necesita para mandar teclas al juego.
3. Elegí el modo y después el mapa. No toques el teclado mientras escribe.

### Notas
- Solo offline / Lumen. No lo uses online.
- Algunos antivirus lo marcan. Es un falso positivo: es una app de Python (PyInstaller) que simula teclas. Todo el código fuente está en este repo.
- Tecla de consola: la de arriba de Tab. Si no abre, cambiá el método en **Ajustes**.

### Compilar desde el código
Necesitás Python 3 para Windows. Poné `build_exe.bat` junto a `Bo7 Zombies Simple Tool.pyw` y hacele doble clic. El `.exe` queda en `dist/`.

---

**Credits / Créditos:** commands and IDs from [Atlas](https://atu-atlas.github.io/BO7/) by atu.
