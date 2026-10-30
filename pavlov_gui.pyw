import os
import sys
import json
import random
import shutil
import traceback
import tkinter as tk
from tkinter import ttk, messagebox

# --- ФИКС ДЛЯ VLC НА WINDOWS ---
if sys.platform.startswith("win"):
    vlc_paths = [
        r"C:\Program Files\VideoLAN\VLC",
        r"C:\Program Files (x86)\VideoLAN\VLC"
    ]
    for p in vlc_paths:
        if os.path.exists(p):
            try:
                os.add_dll_directory(p)
            except Exception:
                pass

try:
    import vlc
    HAS_VLC = True
except ImportError:
    HAS_VLC = False

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

SESSION_FILE = "pavlov_session.json"

# --- ПУТИ К ПАПКАМ ---
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DIR_CORRECT = os.path.join(SCRIPT_DIR, "videos_S_plus")
DIR_INCORRECT = os.path.join(SCRIPT_DIR, "videos_S_minus")
DIR_SOUND_BELL = os.path.join(SCRIPT_DIR, "sound_bell")
DIR_SOUND_BG = os.path.join(SCRIPT_DIR, "sound_background")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "experiment_output")

VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v")
AUDIO_EXTS = (".wav", ".mp3", ".ogg")

# --- СЛОВАРИ ДЛЯ ЛОКАЛИЗАЦИИ ---
TEXTS = {
    "ru": {
        "title": "Эксперимент Павлова",
        "config_title": "Настройка эксперимента",
        "files_note": "Поместите файлы в папки рядом с приложением.",
        "help_btn": "❓ Подробная инструкция",
        "lang_btn": "EN",
        "refresh": "Обновить",
        "count_s_plus": "Целевых (S+): {}",
        "count_s_minus": "Нецелевых (S-): {}",
        "bell_sound": "Звук колокольчика (УС):",
        "bg_sound": "Фоновый звук:",
        "chance": "Шанс колокольчика на S+:",
        "vol_video": "Видео:",
        "vol_bell": "Колокольчик:",
        "vol_bg": "Фон:",
        "btn_start": "Начать эксперимент",
        "btn_prev": "Назад",
        "btn_pause": "Пауза",
        "btn_resume": "Продолжить",
        "btn_next": "Далее",
        "btn_stop": "Завершить",
        "msg_no_video": "Нет видеофайлов в папках:\n{}\n{}",
        "help_text": """СУТЬ ЭКСПЕРИМЕНТА
Это классический эксперимент по изучению условных рефлексов (по И.П. Павлову). Участнику предъявляются визуальные стимулы (видео), разделенные на две категории. Задача испытуемого — научиться их различать.

ТЕРМИНОЛОГИЯ:
• Целевой стимул (S+) — видео, которое подкрепляется.
• Нецелевой стимул (S-) — видео, которое не подкрепляется.
• Условный стимул (УС) — звук колокольчика. Изначально он нейтрален, но при связке с целевым стимулом (S+) становится предвестником «правильного» ответа.

ПОРЯДОК ПОКАЗА ВИДЕО
Программа не просто перемешивает видео, а выстраивает их в определенном порядке для равномерности.
- Если S+ и S- равное количество, они чередуются (S+, S-, S+).
- Если одних больше (например, 1 S+ и 2 S-), они распределяются пропорционально (S-, S-, S+).
- Внутри этих правил сами видео всегда выбираются случайным образом.

ПАПКИ И ФАЙЛЫ
[videos_S_plus] — целевые видео. К ним применяется шанс колокольчика, и они сопровождаются фоновым звуком.
[videos_S_minus] — нецелевые видео. На них никогда не играет колокольчик.

[sound_bell] — аудиофайлы (.wav, .mp3, .ogg) для колокольчика. Если папка пуста, используется встроенный звук.
[sound_background] — аудиофайлы для фона. Играют зациклено во время S+.

ЧТО ЗНАЧИТ «ШАНС КОЛОКОЛЬЧИКА»?
Это вероятность (0-100%), с которой перед S+ прозвучит УС.
- 100% — колокольчик звучит всегда.
- 85% (рекомендуется) — в 15% случаев S+ начнется без звука. Это поддерживает бдительность испытуемого.
- 0% — колокольчик отключен.

УПРАВЛЕНИЕ
- Ползунки громкости всегда доступны внизу экрана.
- Горячие клавиши: Пробел (Пауза), Стрелки (Переключение), Esc (Завершить)."""
    },
    "en": {
        "title": "Pavlov's Experiment",
        "config_title": "Experiment Setup",
        "files_note": "Place files in the folders next to the app.",
        "help_btn": "❓ Detailed Instructions",
        "lang_btn": "RU",
        "refresh": "Refresh",
        "count_s_plus": "Target (S+): {}",
        "count_s_minus": "Non-target (S-): {}",
        "bell_sound": "Bell sound (CS):",
        "bg_sound": "Background sound:",
        "chance": "Bell chance on S+:",
        "vol_video": "Video:",
        "vol_bell": "Bell:",
        "vol_bg": "Background:",
        "btn_start": "Start Experiment",
        "btn_prev": "Previous",
        "btn_pause": "Pause",
        "btn_resume": "Resume",
        "btn_next": "Next",
        "btn_stop": "Stop",
        "msg_no_video": "No video files found in:\n{}\n{}",
        "help_text": """EXPERIMENT OVERVIEW
This is a classic classical conditioning experiment (Pavlovian). The participant is presented with visual stimuli (videos) divided into two categories. The subject's task is to learn to distinguish them.

TERMINOLOGY:
• Target Stimulus (S+) — the video that is reinforced.
• Non-target Stimulus (S-) — the video that is not reinforced.
• Conditioned Stimulus (CS) — the bell sound. Initially neutral, but when paired with S+, it becomes a predictor of the "correct" response.

DISPLAY ORDER
The program doesn't just shuffle videos randomly; it interleaves them proportionally for even distribution.
- If S+ and S- are equal in number, they alternate (S+, S-, S+).
- If one is greater (e.g., 1 S+ and 2 S-), they are distributed proportionally (S-, S-, S+).
- Within these rules, the specific videos are always selected randomly.

FOLDERS AND FILES
[videos_S_plus] — target videos. The bell chance is applied to them, and they are accompanied by background audio.
[videos_S_minus] — non-target videos. The bell never plays for them.

[sound_bell] — audio files (.wav, .mp3, .ogg) for the bell. If empty, a built-in sound is used.
[sound_background] — audio files for the background. Loops during S+.

WHAT DOES "BELL CHANCE" MEAN?
This is the probability (0-100%) that the CS will play before S+.
- 100% — the bell always plays.
- 85% (recommended) — in 15% of cases, S+ starts without the bell. This maintains the subject's vigilance.
- 0% — the bell is disabled.

CONTROLS
- Volume sliders are always available at the bottom.
- Hotkeys: Space (Pause), Arrows (Switch), Esc (Stop)."""
    }
}

class PavlovApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        self.root.minsize(850, 600)

        self.lang = "ru"
        
        self._init_folders()

        self.playlist = []
        self.current_index = -1
        self.is_experiment_running = False

        self.bell_sound = None
        self.bg_sound = None
        
        self.vlc_instance = None
        self.vlc_player = None
        if HAS_VLC:
            try:
                self.vlc_instance = vlc.Instance("--no-video-title-show", "--quiet", "--no-xlib")
                self.vlc_player = self.vlc_instance.media_player_new()
            except Exception:
                pass

        if HAS_PYGAME:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                pygame.mixer.set_num_channels(8)
            except Exception:
                pass

        self._build_ui()
        self._update_ui_texts()
        self._scan_files()

        self.root.after(100, self._poll_end)

        self.root.bind("<space>", lambda e: self._toggle_play())
        self.root.bind("<Right>", lambda e: self._next_video())
        self.root.bind("<Left>", lambda e: self._prev_video())
        self.root.bind("<Escape>", lambda e: self._finish() if self.is_experiment_running else None)

    def _init_folders(self):
        for d in [DIR_CORRECT, DIR_INCORRECT, DIR_SOUND_BELL, DIR_SOUND_BG, OUTPUT_DIR]:
            os.makedirs(d, exist_ok=True)

    def _change_lang(self):
        self.lang = "en" if self.lang == "ru" else "ru"
        self._update_ui_texts()

    def _update_ui_texts(self):
        t = TEXTS[self.lang]
        self.root.title(t["title"])
        self.config_frame.config(text=t["config_title"])
        self.lbl_note.config(text=t["files_note"])
        self.btn_help.config(text=t["help_btn"])
        self.btn_lang.config(text=t["lang_btn"])
        self.btn_refresh.config(text=t["refresh"])
        
        self.lbl_bell_sound.config(text=t["bell_sound"])
        self.lbl_bg_sound.config(text=t["bg_sound"])
        self.lbl_chance.config(text=t["chance"])
        
        self.lbl_vol_video.config(text=t["vol_video"])
        self.lbl_vol_bell.config(text=t["vol_bell"])
        self.lbl_vol_bg.config(text=t["vol_bg"])
        
        if self.is_experiment_running:
            self.btn_pause.config(text=t["btn_resume"] if not self.vlc_player.is_playing() else t["btn_pause"])
            self.btn_prev.config(text=t["btn_prev"])
            self.btn_next.config(text=t["btn_next"])
            self.btn_stop.config(text=t["btn_stop"])
        else:
            self.btn_start.config(text=t["btn_start"])
            
        self._scan_files()

    def _show_help(self):
        help_win = tk.Toplevel(self.root)
        help_win.title(TEXTS[self.lang]["help_btn"].replace("❓ ", ""))
        help_win.geometry("700x600")
        help_win.transient(self.root)
        help_win.grab_set()

        text = tk.Text(help_win, wrap="word", padx=15, pady=15, font=("Segoe UI", 11))
        text.pack(fill="both", expand=True)
        text.insert("1.0", TEXTS[self.lang]["help_text"])
        text.config(state="disabled")

        ttk.Button(help_win, text="OK", command=help_win.destroy).pack(pady=10)

    def _scan_files(self):
        self.videos_correct = [f for f in os.listdir(DIR_CORRECT) if f.lower().endswith(VIDEO_EXTS)]
        self.videos_incorrect = [f for f in os.listdir(DIR_INCORRECT) if f.lower().endswith(VIDEO_EXTS)]
        
        t = TEXTS[self.lang]
        self.lbl_count.config(text=f"{t['count_s_plus'].format(len(self.videos_correct))} | {t['count_s_minus'].format(len(self.videos_incorrect))}")
        
        bells = [f for f in os.listdir(DIR_SOUND_BELL) if f.lower().endswith(AUDIO_EXTS)]
        bgs = [f for f in os.listdir(DIR_SOUND_BG) if f.lower().endswith(AUDIO_EXTS)]
        
        self.bell_combo['values'] = ["(Built-in / Встроенный)"] + bells
        if not self.bell_combo.get():
            self.bell_combo.current(0)
            
        self.bg_combo['values'] = ["(None / Нет)"] + bgs
        if not self.bg_combo.get():
            self.bg_combo.current(0)

    def _build_ui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self.config_frame = ttk.LabelFrame(self.main_frame, text="")
        self.config_frame.pack(fill="x", pady=(0, 10))

        header_row = ttk.Frame(self.config_frame)
        header_row.pack(fill="x", padx=10, pady=(5, 5))
        
        self.lbl_note = ttk.Label(header_row, text="", foreground="gray")
        self.lbl_note.pack(side="left")
        
        self.btn_lang = ttk.Button(header_row, text="", width=4, command=self._change_lang)
        self.btn_lang.pack(side="right", padx=5)
        
        self.btn_help = ttk.Button(header_row, text="", command=self._show_help)
        self.btn_help.pack(side="right", padx=5)
        
        row1 = ttk.Frame(self.config_frame)
        row1.pack(fill="x", padx=10, pady=5)
        
        self.lbl_count = ttk.Label(row1, text="...")
        self.lbl_count.pack(side="left")
        self.btn_refresh = ttk.Button(row1, text="", command=self._scan_files)
        self.btn_refresh.pack(side="left", padx=15)
        
        row2 = ttk.Frame(self.config_frame)
        row2.pack(fill="x", padx=10, pady=5)
        
        self.lbl_bell_sound = ttk.Label(row2, text="")
        self.lbl_bell_sound.pack(side="left")
        self.bell_combo = ttk.Combobox(row2, state="readonly", width=25)
        self.bell_combo.pack(side="left", padx=5)
        
        self.lbl_bg_sound = ttk.Label(row2, text="")
        self.lbl_bg_sound.pack(side="left", padx=(15, 0))
        self.bg_combo = ttk.Combobox(row2, state="readonly", width=25)
        self.bg_combo.pack(side="left", padx=5)

        row3 = ttk.Frame(self.config_frame)
        row3.pack(fill="x", padx=10, pady=(5, 10))
        
        self.lbl_chance = ttk.Label(row3, text="")
        self.lbl_chance.pack(side="left")
        self.bell_prob_var = tk.IntVar(value=85)
        ttk.Spinbox(row3, from_=0, to=100, textvariable=self.bell_prob_var, width=5).pack(side="left", padx=5)
        ttk.Label(row3, text="%").pack(side="left")

        self.video_frame = tk.Frame(self.main_frame, bg="black")
        self.video_frame.pack(fill="both", expand=True)
        
        self.root.update()
        if self.vlc_player is not None:
            try:
                self.vlc_player.set_hwnd(self.video_frame.winfo_id())
            except Exception:
                pass

        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(fill="x", pady=(10, 0))

        vol_row = ttk.Frame(self.bottom_frame)
        vol_row.pack(fill="x", pady=(0, 10))

        self.lbl_vol_video = ttk.Label(vol_row, text="")
        self.lbl_vol_video.pack(side="left")
        self.video_volume_var = tk.IntVar(value=80)
        ttk.Scale(vol_row, from_=0, to=100, orient="horizontal", variable=self.video_volume_var, command=self._on_video_volume).pack(side="left", fill="x", expand=True, padx=(5, 5))
        self.lbl_val_video = ttk.Label(vol_row, text="80", width=3)
        self.lbl_val_video.pack(side="left", padx=(0, 15))
        
        self.lbl_vol_bell = ttk.Label(vol_row, text="")
        self.lbl_vol_bell.pack(side="left")
        self.bell_volume_var = tk.IntVar(value=70)
        ttk.Scale(vol_row, from_=0, to=100, orient="horizontal", variable=self.bell_volume_var, command=self._on_bell_volume).pack(side="left", fill="x", expand=True, padx=(5, 5))
        self.lbl_val_bell = ttk.Label(vol_row, text="70", width=3)
        self.lbl_val_bell.pack(side="left", padx=(0, 15))

        self.lbl_vol_bg = ttk.Label(vol_row, text="")
        self.lbl_vol_bg.pack(side="left")
        self.bg_volume_var = tk.IntVar(value=20)
        ttk.Scale(vol_row, from_=0, to=100, orient="horizontal", variable=self.bg_volume_var, command=self._on_bg_volume).pack(side="left", fill="x", expand=True, padx=(5, 5))
        self.lbl_val_bg = ttk.Label(vol_row, text="20", width=3)
        self.lbl_val_bg.pack(side="left")

        ctrl_row = ttk.Frame(self.bottom_frame)
        ctrl_row.pack(fill="x")
        
        btn_style = {"padding": 5}
        
        self.btn_start = ttk.Button(ctrl_row, text="", command=self._start_experiment, **btn_style)
        self.btn_start.pack(side="left")
        
        self.btn_prev = ttk.Button(ctrl_row, text="", command=self._prev_video, **btn_style)
        self.btn_pause = ttk.Button(ctrl_row, text="", command=self._toggle_play, **btn_style)
        self.btn_next = ttk.Button(ctrl_row, text="", command=self._next_video, **btn_style)
        self.btn_stop = ttk.Button(ctrl_row, text="", command=self._finish, **btn_style)

    def _start_experiment(self):
        self._scan_files()
        t = TEXTS[self.lang]
        if not self.videos_correct and not self.videos_incorrect:
            messagebox.showwarning("!", t["msg_no_video"].format(DIR_CORRECT, DIR_INCORRECT))
            return

        b_choice = self.bell_combo.get()
        self.bell_sound = None
        if "Built-in" in b_choice or "Встроенный" in b_choice:
            self.bell_sound = self._generate_bell()
        elif b_choice:
            try:
                self.bell_sound = pygame.mixer.Sound(os.path.join(DIR_SOUND_BELL, b_choice))
            except Exception: pass
            
        bg_choice = self.bg_combo.get()
        self.bg_sound = None
        if bg_choice and "None" not in bg_choice and "Нет" not in bg_choice:
            try:
                self.bg_sound = pygame.mixer.Sound(os.path.join(DIR_SOUND_BG, bg_choice))
            except Exception: pass

        bell_prob = self.bell_prob_var.get() / 100.0
        self.playlist = []

        for f in self.videos_correct:
            full = os.path.join(DIR_CORRECT, f)
            has_bell = random.random() < bell_prob
            self.playlist.append({"path": full, "filename": f, "is_correct": True, "has_bell": has_bell})

        for f in self.videos_incorrect:
            full = os.path.join(DIR_INCORRECT, f)
            self.playlist.append({"path": full, "filename": f, "is_correct": False, "has_bell": False})

        # === НОВЫЙ АЛГОРИТМ ЧЕРЕДОВАНИЯ ===
        pl_plus = [item for item in self.playlist if item["is_correct"]]
        pl_minus = [item for item in self.playlist if not item["is_correct"]]
        
        random.shuffle(pl_plus)
        random.shuffle(pl_minus)
        
        self.playlist = []
        total = len(pl_plus) + len(pl_minus)
        
        if total > 0:
            ratio = len(pl_plus) / total
            count_plus = 0
            count_minus = 0
            
            for i in range(total):
                expected = (i + 1) * ratio
                # Вставляем S+, если мы еще не достигли ожидаемого количества
                if count_plus < expected - 0.001 and count_plus < len(pl_plus):
                    self.playlist.append(pl_plus[count_plus])
                    count_plus += 1
                # Иначе вставляем S- (если они еще остались)
                elif count_minus < len(pl_minus):
                    self.playlist.append(pl_minus[count_minus])
                    count_minus += 1
                # Если S- закончились, добиваем оставшимися S+
                else:
                    self.playlist.append(pl_plus[count_plus])
                    count_plus += 1
        # ==================================

        self.current_index = 0

        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(self.playlist, f, ensure_ascii=False, indent=2)

        self.config_frame.pack_forget()
        self.btn_start.pack_forget()
        self.btn_prev.pack(side="left", padx=5)
        self.btn_pause.pack(side="left", padx=5)
        self.btn_next.pack(side="left", padx=5)
        self.btn_stop.pack(side="left", padx=20)

        self.is_experiment_running = True
        self._update_ui_texts()
        self._play_current()

    def _finish(self):
        self.is_experiment_running = False
        self._stop()
        self.current_index = -1
        
        self.btn_prev.pack_forget()
        self.btn_pause.pack_forget()
        self.btn_next.pack_forget()
        self.btn_stop.pack_forget()
        
        self.config_frame.pack(fill="x", pady=(0, 10), before=self.video_frame)
        self.btn_start.pack(side="left")
        self._update_ui_texts()

    def _play_current(self):
        if self.current_index < 0 or self.current_index >= len(self.playlist): return
        item = self.playlist[self.current_index]
        
        if HAS_PYGAME and pygame.mixer.get_init(): 
            pygame.mixer.stop()

        if item["is_correct"] and self.bg_sound:
            self.bg_sound.set_volume(self.bg_volume_var.get() / 100.0)
            self.bg_sound.play(loops=-1)

        if self.vlc_player is not None:
            media = self.vlc_instance.media_new(item["path"])
            self.vlc_player.set_media(media)
            self.vlc_player.play()
            vol = self.video_volume_var.get()
            self.root.after(50, lambda: self.vlc_player.audio_set_volume(vol))

        if item["has_bell"]:
            self.root.after(50, self._wait_and_play_bell)
        
        self.btn_pause.config(text=TEXTS[self.lang]["btn_pause"])

    def _wait_and_play_bell(self):
        if self.vlc_player and not self.vlc_player.is_playing():
            self.root.after(20, self._wait_and_play_bell)
            return
        
        if HAS_PYGAME and self.bell_sound:
            self.bell_sound.set_volume(self.bell_volume_var.get() / 100.0)
            self.bell_sound.play()

    def _toggle_play(self):
        if self.vlc_player is None or not self.is_experiment_running: return
        t = TEXTS[self.lang]
        if self.vlc_player.is_playing():
            self.vlc_player.pause()
            if HAS_PYGAME and pygame.mixer.get_init(): pygame.mixer.pause()
            self.btn_pause.config(text=t["btn_resume"])
        else:
            self.vlc_player.play()
            if HAS_PYGAME and pygame.mixer.get_init(): pygame.mixer.unpause()
            self.btn_pause.config(text=t["btn_pause"])

    def _next_video(self):
        if not self.playlist or not self.is_experiment_running: return
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self._play_current()
        else:
            self._finish()

    def _prev_video(self):
        if not self.playlist or not self.is_experiment_running: return
        if self.current_index > 0:
            self.current_index -= 1
            self._play_current()

    def _stop(self):
        if self.vlc_player is not None: self.vlc_player.stop()
        if HAS_PYGAME and pygame.mixer.get_init(): pygame.mixer.stop()

    def _poll_end(self):
        try:
            if (self.vlc_player and self.playlist and self.current_index >= 0 and self.is_experiment_running
                    and self.vlc_player.get_state() == vlc.State.Ended):
                if self.current_index < len(self.playlist) - 1:
                    self.current_index += 1
                    self._play_current()
                else:
                    self._finish()
                    return
        except Exception:
            pass
        self.root.after(100, self._poll_end)

    def _on_video_volume(self, value):
        v = int(float(value))
        self.lbl_val_video.config(text=str(v))
        if self.vlc_player is not None: self.vlc_player.audio_set_volume(v)

    def _on_bell_volume(self, value):
        v = int(float(value))
        self.lbl_val_bell.config(text=str(v))
        if self.bell_sound is not None: self.bell_sound.set_volume(v / 100.0)

    def _on_bg_volume(self, value):
        v = int(float(value))
        self.lbl_val_bg.config(text=str(v))
        if self.bg_sound is not None: self.bg_sound.set_volume(v / 100.0)

    def _generate_bell(self):
        if not (HAS_PYGAME and HAS_NUMPY): return None
        sr = 44100
        duration = 1.5
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        env = np.exp(-5 * t / duration)
        wave = (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1760 * t)) * env
        pcm = (wave * 32767 * 0.8).astype(np.int16)
        stereo = np.column_stack([pcm, pcm])
        try:
            return pygame.sndarray.make_sound(stereo)
        except Exception:
            return None

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = PavlovApp(root)
        root.mainloop()
    except Exception as e:
        with open("error_log.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        messagebox.showerror("Критическая ошибка / Critical Error", f"{e}\n\nПодробности в error_log.txt / Details in error_log.txt")