'''
Author: Night-stars-1 nujj1042633805@gmail.com
Date: 2023-05-19 16:04:28
LastEditors: Night-stars-1 nujj1042633805@gmail.com
LastEditTime: 2023-05-28 18:43:06
Description: 

Copyright (c) 2023 by Night-stars-1, All Rights Reserved. 
'''
import os
import re
import math
import cn2an
import questionary
import pygetwindow as gw

from copy import deepcopy
from xpinyin import Pinyin
from questionary import Validator, ValidationError
from typing import List
from pynput.keyboard import Controller as KeyboardController
from threading import Thread
from ultralytics.nn.tasks import  attempt_load_weights

from .calculated import *
from .config import get_file, read_json_file, modify_json_file, CONFIG_FILE_NAME
from .log import log
from .requests import webhook_and_log
#from .yolo import predict
from .adb import ADB

class Simulated_Universe:
    def __init__(self, platform="PC",order="127.0.0.1:62001", adb_path="temp\\adb\\adb"):
        """
        参数: 
            :param platform: 运行设备
        """
        self.platform = platform # 运行设备
        self.open_map = read_json_file(CONFIG_FILE_NAME).get("open_map", "m")
        self.window = gw.getWindowsWithTitle('崩坏：星穹铁道')[0] if platform == "PC" else None
        self.hwnd = self.window._hWnd if platform == "PC" else None
        self.map_list = []
        self.map_list_map = {}

        self.adb = ADB(order, adb_path)
        self.calculated = calculated(platform,order)
        self.p = Pinyin()
        self.keyboard = KeyboardController()
        #self.model = attempt_load_weights("./temp/model/best.pt")

    def read_role(self):
        """
        说明：
            读取角色
        返回:
            角色列表
        """
        self.role_list = get_file('./temp/Simulated_Universe/role')
        self.role_list = [i.split('.jpg')[0] for i in self.role_list]
        log.debug(self.role_list)
        return self.role_list
    
    def choose_level(self, level: int, start: int, pos):
        """
        说明：
            选择关卡
        参数：
            :param level: 第几个世界
            :param start: 当前世界
            :param pos: 文字坐标
        """
        if level > start:
            for i in range(abs(level - start)):
                if self.platform == "PC":
                    self.calculated.scroll(1)
                elif self.platform == "模拟器":
                    self.adb.input_swipe((919, 617), (919, 908), 100)
        elif level < start:
            for i in range(abs(level - start)):
                if self.platform == "PC":
                    self.calculated.scroll(-1)
                elif self.platform == "模拟器":
                    self.adb.input_swipe((925, 650), (925, 394), 100)
        if self.platform == "PC":
            time.sleep(0.5)
            self.calculated.Relative_click((60, 50))
        elif self.platform == "模拟器":
            time.sleep(0.5)
            self.adb.input_tap((895, 394))
        start_time = time.time()
        while True:
            if self.platform == "PC":
                left, top, right, bottom = self.window.left, self.window.top, self.window.right, self.window.bottom
                img_fp = ImageGrab.grab((left, top, right, bottom))
                text, pos = self.calculated.ocr_pos(img_fp, "下载初始角色")
                if pos:
                    self.calculated.Click((left+pos[0], top+pos[1]))
                    break
            elif self.platform == "模拟器":
                img_fp = self.adb.screencast()
                text, pos = self.calculated.ocr_pos(img_fp, "下载初始角色")
                if pos:
                    self.adb.input_tap(pos)
                    break
            if time.time() - start_time > 10:
                log.info("识别超时")
                break

    def choose_role(self, roles: list):
        """
        说明：
            选择角色
        参数：
            :param roles: 角色列表
        """
        time.sleep(1)
        if self.platform == "PC":
            left, top, right, bottom = self.window.left, self.window.top, self.window.right, self.window.bottom
            img_fp = ImageGrab.grab((left, top, right-(right-left)/100*70, bottom))
        elif self.platform == "模拟器":
            img_fp = self.adb.screencast()
        start_time = time.time()
        while True:
            for role in roles:
                role_py = self.p.get_pinyin(role,'')
                target = cv.imread(f"./temp/Simulated_Universe/role/mnq/{role_py}.png")
                result = self.calculated.scan_screenshot(target, img_fp)
                print(role+":"+str(result['max_val']))
                if result['max_val'] > 0.90:
                    roles.remove(role)
                    #points = self.calculated.calculated(result, img.shape)
                    if self.platform == "PC":
                        self.calculated.Click((result['max_loc'][0]+10, result['max_loc'][1]+10))
                    elif self.platform == "模拟器":
                        self.adb.input_tap((result['max_loc'][0]+10, result['max_loc'][1]+10))
                    time.sleep(0.1)
            if len(roles) == 0:
                break
            elif time.time() - start_time > 15:
                log.info("识别超时")
                break

    def choose_presets(self, choose_presets):
        """
        说明：
            设置预设
        参数：
            :param choose_presets: 选项
        """
        presets_list = read_json_file(CONFIG_FILE_NAME).get("presets", [])
        if choose_presets == '设置预设':
            role_presets_num = int(questionary.text("请输入预设数量：").ask())
            for r in range(1, role_presets_num + 1):
                log.info(f'当前是第{r}只队伍预设')
                roles = ['三月七', '丹恒', '佩拉', '姬子', '娜塔莎', '婷云', '布洛尼亚', '希儿', '希露瓦', '彦卿', '景元', '杰帕德', '桑博', '火主', '火主1', '物主', '瓦尔特', '素裳', '艾丝妲', '虎克', '阿兰', '青雀', '黑塔']
                role_list = questionary.checkbox('请选择角色',choices=roles,validate=lambda a: (
                                            True if len(a) == 5 else "请选择5名角色"
                                        )).ask()
                presets_list.append(role_list)
                modify_json_file(CONFIG_FILE_NAME, "presets", presets_list)

    def choose_bless(self, bless:str = "巡猎"):
        """
        说明：
            选择祝福
        参数：
            :param bless: 命途
        """
        start_time = time.time()
        while True:
            result = self.calculated.ocr_click(f"「{bless}」", 3, 2)
            if not result:
                bless_list = ['「存护」', '「记忆」', '「虚无」', '「丰饶」', '「巡猎」', '「毁灭」', '「欢愉」']
                bless_list.remove(f"「{bless}」")
                for bless in bless_list:
                    result = self.calculated.ocr_click(bless, 3, 2)
                    if result:
                        break
            result = self.calculated.part_ocr((6,10,89,88))
            if "选择祝福" not in result:
                break
            elif time.time() - start_time > 15:
                log.info("识别超时")
                break

    def choose_event(self):
        """
        说明：
            选择事件
        """
        start_time = time.time()
        while True:
            result = self.calculated.ocr_click("「巡猎」", 3, 2)
            if not result:
                event_choose_list = ["选择","进入战斗"]
                event = ["选择"]
                log.info(set(event_choose_list).intersection(set(event)))
            result = self.calculated.part_ocr((6,10,89,88))
            if "选择事件" not in result:
                break
            elif time.time() - start_time > 15:
                log.info("识别超时")
                break

    def auto_map(self, start = 1, choose_list = []):
        #self.calculated.part_ocr((6,10,89,88))
        #self.calculated.fighting(type=1)
        roles = choose_list[0][0:3]
        fate = choose_list[1]
        #log.info(self.match_scr(self.exist_minimap()))
        #log.info(get_rolepos('47.png'))
        '''
        path = [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),(0,9),(1,9)]
        self.calculated.path_move(path)
        img_fp, left, top, right, bottom, width, length = self.calculated.take_screenshot((40,45,55,60))
        text, pos = self.calculated.ocr_pos(img_fp)
        level = cn2an.cn2an(re.findall(r"第(.*)世界", text)[0])
        self.choose_level(level, start, pos, platform)
        self.choose_role(roles, platform)
        if platform == "PC":
            self.calculated.Relative_click((85, 90))
        elif platform == "模拟器":
            os.system(f"adb -s {self.order} shell input tap 1020 654")
        self.calculated.ocr_click("O确认", 2)
        time.sleep(0.5)
        self.calculated.ocr_click(fate, 3, 2)
        time.sleep(1)
        self.calculated.ocr_click("确认命途", 3, 2)
        time.sleep(5)
        self.calculated.wait_join(platform=platform)
        self.calculated.ocr_click("获得150宇宙碎片", 3, 2)
        self.calculated.ocr_click("确认", 3, 3)
        self.choose_bless(fate, platform=platform)
        log.info(get_rolepos("44.png", platform=platform))
        '''
        '''
        t1 = Thread(target=self.start_predict)
        t1.start()
        '''


