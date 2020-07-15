#! /usr/bin/env python3
import csv
import curses
import curses.panel as panel
from datetime import datetime, timedelta
import os
import random

working_path = os.path.expanduser("~/.vokabeln")

class Header:
    def __init__(self, stdscr, title, menu):
        h, self.w = stdscr.getmaxyx();
        self.h = 5
        self.win = curses.newwin(self.h, self.w, 0, 0);
        self.panel = panel.new_panel(self.win);
        self.menu = menu;
        self.active_menu = 0;
        self.title = title;

        self.draw();

    def change_menu(self, v):
        self.active_menu += v;
        if self.active_menu < 0:
            self.active_menu = 0;
        elif self.active_menu > len(self.menu)-1:
            self.active_menu = len(self.menu)-1;
        self.draw()

    def get_fach(self):
        return self.menu[self.active_menu];

    def draw(self):
        self.win.clear()
        self.win.addstr(0, 0, self.title);
        xposarr = [3];
        self.win.hline(4, 0, curses.ACS_HLINE, 2);
        for i, title in enumerate(self.menu):
            xposarr.append(xposarr[i]+len(title)+3);
            self.win.addstr(3,xposarr[i], self.menu[i]);
            if i == self.active_menu:
                self.win.addch(4, xposarr[i]-2, curses.ACS_LRCORNER);
                self.win.addch(3, xposarr[i]-2, curses.ACS_VLINE);
                self.win.addch(2, xposarr[i]-2, curses.ACS_ULCORNER);
                self.win.hline(2, xposarr[i]-1, curses.ACS_HLINE, len(title)+2);
                self.win.addch(2, xposarr[i]+len(title)+1, curses.ACS_URCORNER);
                self.win.addch(3, xposarr[i]+len(title)+1, curses.ACS_VLINE);
                self.win.addch(4, xposarr[i]+len(title)+1, curses.ACS_LLCORNER);
            else:
                self.win.hline(4, xposarr[i]-1, curses.ACS_HLINE, len(title)+3);
        self.win.hline(4, xposarr[len(self.menu)]-1, curses.ACS_HLINE, self.w-xposarr[len(self.menu)]+1);
        self.show_changes()

    def show_changes(self):
        panel.update_panels();
        curses.doupdate();

class Body:
    def __init__(self, stdscr, fach):
        h, self.w = stdscr.getmaxyx();
        self.h = h - 5;
        self.win = curses.newpad(1000,200);
        self.fach = fach;
        self.curser = 0;
        self.vokabeln = [];
        self.xpos = 15;
        self.ypos = 0;
        self.load();
        self.draw();

    def load(self):
        try:
            with open(os.path.join(working_path, self.fach + ".csv"), 'r') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter='|');
                self.vokabeln = [];
                self.xpos = 15;
                for row in csv_reader:
                    if len(row) > 1:
                        self.vokabeln.append(row);
                        if self.xpos < len(row[0])+5:
                            self.xpos = len(row[0])+5;
        except:
            self.vokabeln = []
            self.show_changes();

    def save(self):
        with open(os.path.join(working_path, self.fach + ".csv"), 'w') as csv_file:
            for row in self.vokabeln:
                for i, word in enumerate(row):
                    if type(word) is str:
                        if not i == 0:
                            csv_file.write('|');
                        csv_file.write(word);
                csv_file.write("\n");

    def add(self):
        add_win = curses.newwin(1, self.w, curses.LINES-1, 0)
        add_pan = panel.new_panel(add_win);
        add_win.addstr(0, 0,self.fach + ": ");
        curses.curs_set(2);
        curses.echo();
        fach = add_win.getstr()
        fach = fach.decode('utf-8');
        add_win.hline(0, 0,' ',self.w);
        add_win.addstr(0, 0,"Deutsch: ");
        deutsch = add_win.getstr()
        deutsch = deutsch.decode('utf-8');
        curses.curs_set(0);
        curses.noecho();
        if len(fach) and len(deutsch):
            self.vokabeln.append([fach, deutsch, datetime.today().strftime("%-d.%m.%Y"),"1"]);
        self.change_curser_to(len(self.vokabeln)-1)
        if self.xpos < len(fach)+5:
            self.xpos = len(fach)+5;

        self.draw();

    def edit(self):
        edit_win = curses.newwin(10, 60, self.h//2, self.w//2-30);
        edit_panel = panel.new_panel(edit_win);
        h, w = edit_win.getmaxyx();
        edit_win.border();
        edit_win.addstr(0,2,"editmode");
        edit_win.addstr(3,2,"1: " + self.fach + ": " + self.vokabeln[self.curser][0]);
        edit_win.addstr(6,2,"2: Deutsch: " + self.vokabeln[self.curser][1]);
        self.show_changes();
        while 1:
            c = edit_win.getch();
            if c == ord('1'):
                edit_win.addstr(4,5+len(self.fach),": ");
                curses.curs_set(2);
                curses.echo();
                self.vokabeln[self.curser][0] = edit_win.getstr().decode('utf-8');
                curses.curs_set(0);
                curses.noecho();
            elif c == ord('2'):
                edit_win.addstr(7,12,": ");
                curses.curs_set(2);
                curses.echo();
                self.vokabeln[self.curser][1] = edit_win.getstr().decode('utf-8');
                curses.curs_set(0);
                curses.noecho();
            elif c == ord('q') or ord('h'):
                break
        self.draw();

        return;

    def delete(self):
        del self.vokabeln[self.curser];
        self.change_curser(-1);
        self.draw();

    def learn(self):
        self.save(); # Save Vocablurary for Safetyreasins
        falsch = [];
        false_i = [];
        learn_ids=[];
        #learn_vokabeln = self.vokabeln;
        learn_vokabeln = [];
        now = datetime.now();
        for i, row in enumerate(self.vokabeln):
            row.append(i);
        for row in self.vokabeln:
            d = datetime.strptime(row[2], "%d.%m.%Y");
            today = datetime.today();
            dif = today - d;
            if dif.days >= 0:
                learn_vokabeln.append(row);
                learn_ids.append(row[-1]);
        self.win.clear();
        learn_win = curses.newwin(10, 60,self.h//2, self.w//2-30);
        learn_panel = panel.new_panel(learn_win);
        h, w = learn_win.getmaxyx();
        while len(learn_vokabeln) > 0:
            learn_win.clear();
            learn_win.border();
            i = random.randrange(len(learn_vokabeln));
            learn_win.addstr(h-4,1, "Level: {}".format(learn_vokabeln[i][3]));
            learn_win.addstr(h-3,1, "Falsch: {}".format(len(falsch)));
            learn_win.addstr(h-2,1, "Verbleibent: {}".format(len(learn_vokabeln)));
            learn_win.addstr(1,1,learn_vokabeln[i][1], curses.A_BOLD);
            learn_win.addstr(h-5, 5, self.fach + ": ",curses.A_BOLD);
            self.show_changes()
            curses.curs_set(2);
            curses.echo();
            inp = learn_win.getstr().decode('utf-8');
            curses.curs_set(0);
            curses.noecho();
            if inp == ":q":
                for word in learn_vokabeln:
                    false_i.append(word[-1])
                self.load()
                return
            elif inp == learn_vokabeln[i][0]:
                del learn_vokabeln[i];
            else:
                falsch.append([inp, learn_vokabeln[i][0], learn_vokabeln[i][1]]);
                false_i.append(learn_vokabeln[i][-1]);
                learn_win.border();
                learn_win.addstr(h-4,1, "Level: {}".format(learn_vokabeln[i][3]));
                learn_win.addstr(h-3,1, "Falsch: {}".format(len(falsch)));
                learn_win.addstr(h-2,1, "Verbleibent: {}".format(len(learn_vokabeln)));
                learn_win.addstr(1,1,learn_vokabeln[i][1], curses.A_BOLD);
                learn_win.addstr(2,1,inp,curses.color_pair(2));
                learn_win.addstr(3,1,learn_vokabeln[i][0],curses.color_pair(1));
                self.show_changes();
                if learn_win.getch() == ord('q'):
                    for word in learn_vokabeln:
                        false_i.append(word[-1])
                    self.load()
                    return
        with open(os.path.join(working_path, self.fach + ".log"), 'a') as logfile:
            print("Du hast am {} um {} {} Fehler gemacht:".format(now.strftime("%-d.%m.%Y"), now.strftime("%H:%M"),len(falsch)), file=logfile);
            for row in falsch:
                print("\t {} -> {}, {}".format(row[0], row[1], row[-1]), file=logfile);
        self.load();
        for i,row in enumerate(self.vokabeln):
            if i in learn_ids:
                if i not in false_i:
                    if row[3] == "1":
                        d = now + timedelta(days=1)
                        row[2] = d.strftime("%d.%m.%Y");
                        row[3] = "2";
                    elif row[3] == "2":
                        d = now + timedelta(days=2);
                        row[2] = d.strftime("%d.%m.%Y");
                        row[3] = "3";
                    elif row[3] == "3":
                        d = now + timedelta(days=4);
                        row[2] = d.strftime("%d.%m.%Y");
                        row[3] = "4";
                    elif row[3] == "4":
                        d = now + timedelta(days=10);
                        row[2] = d.strftime("%d.%m.%Y");
                        row[3] = "3";
                    elif row[3] == "5":
                        d = now + timedelta(days=30);
                        row[2] = d.strftime("%d.%m.%Y");
                        row[3] = "3";
                    else:
                        d = now + timedelta(days=90);
                        row[2] = d.strftime("%d.%m.%Y");
                else:
                    row[2] = now.strftime('%d.%m.%Y');
                    row[3] = "1"

        self.save();
        self.draw();
        return;

    def draw(self):
        self.win.clear();
        if len(self.vokabeln):
            for i, vokabel in enumerate(self.vokabeln):
                if i == self.curser:
                    self.win.attron(curses.A_REVERSE);
                    self.win.hline(i,0,' ', self.w);
                self.win.addstr(i, 3, vokabel[0]);
                self.win.addstr(i, self.xpos, vokabel[1]);
                if i == self.curser:
                    self.win.attroff(curses.A_REVERSE);
        else:
            self.win.addstr(self.h-1, 0, "File: " + self.fach +".csv not found");
        self.show_changes();

    def change_curser(self, v):
        self.curser += v;
        if self.curser < 0:
            self.curser = 0;
        elif self.curser > len(self.vokabeln)-1:
            self.curser = len(self.vokabeln)-1;
        if self.curser - self.ypos > self.h-1:
            self.ypos += 1;
        elif self.curser - self.ypos < 0:
            self.ypos += -1;
        self.draw()

    def change_curser_to(self, v):
        self.curser = v;
        if self.curser - self.ypos > self.h-1:
            self.ypos += 1;
        elif self.curser - self.ypos < 0:
            self.ypos += -1;

    def change_fach(self, fach):
        self.save();
        self.fach = fach;
        self.change_curser_to(0);
        self.load();
        self.draw();

    def show_changes(self):
        self.win.refresh(self.ypos,0,5,0,curses.LINES-1,curses.COLS-1);
        panel.update_panels();
        curses.doupdate();

def main(stdscr):
    curses.init_pair(1,curses.COLOR_GREEN,curses.COLOR_BLACK);
    curses.init_pair(2,curses.COLOR_RED,curses.COLOR_BLACK);
    curses.curs_set(0);
    header = Header(stdscr, "Vokabel Program | q:quit", ["English", "Französisch", "Biologie"]);
    body = Body(stdscr, header.get_fach());
    stdscr.refresh();
    while 1:
        c = stdscr.getch();
        if c == ord('q'):
            body.save();
            quit();
        elif c == ord('h'):
            header.change_menu(-1);
            body.change_fach(header.get_fach());
        elif c == ord('l'):
            header.change_menu(1);
            body.change_fach(header.get_fach());
        elif c == ord('j'):
            body.change_curser(1);
        elif c == ord('k'):
            body.change_curser(-1);
        elif c == ord('a'):
            body.add(); #Fügt eine neue Vokabel hinzu
        elif c == ord('i'):
            body.edit();
        elif c == ord('L'):
            body.learn();
            body.draw();
        elif c == ord('d'):
            if stdscr.getch() == ord('d'):
                body.delete();
        stdscr.refresh();

def test(stdscr):
    pad = curses.newpad(100, 200)
    # These loops fill the pad with letters; addch() is
    # explained in the next section
    for y in range(0, 99):
        for x in range(0, 199):
            pad.addch(y,x, ord('a') + (x*x+y*y) % 26)

    # Displays a section of the pad in the middle of the screen.
    # (0,0) : coordinate of upper-left corner of pad area to display.
    # (5,5) : coordinate of upper-left corner of window area to be filled
    #         with pad content.
    # (20, 75) : coordinate of lower-right corner of window area to be
    #          : filled with pad content.
    pad.refresh( 1,0, 5,0, curses.LINES-1,curses.COLS-1)
    pad.getch()

if __name__ == '__main__':
    curses.wrapper(main)
