import time
import re
import os
import numpy as np
import zhinst.utils
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.pyplot import Figure
import matplotlib.pyplot as plt

import tkinter as tk
import threading as th

import sys
import clr
import System
import ctypes

assembly_path = r"C:\Program Files\Thorlabs\Kinesis"
sys.path.append(assembly_path)

clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
clr.AddReference("Thorlabs.MotionControl.GenericMotorCLI")
clr.AddReference("Thorlabs.MotionControl.Tools.Common")
clr.AddReference("Thorlabs.MotionControl.Tools.Logging")
clr.AddReference("Thorlabs.MotionControl.KCube.DCServoCLI ")

from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.KCube.DCServoCLI import *

from Thorlabs.MotionControl.GenericMotorCLI.ControlParameters import *
from Thorlabs.MotionControl.GenericMotorCLI.AdvancedMotor import *
from Thorlabs.MotionControl.GenericMotorCLI.KCubeMotor import *
from Thorlabs.MotionControl.GenericMotorCLI.Settings import *



#创建会话
def create_session(devid):
    apilevel_example = 6
    try:

        device_id = 'dev4346'
        err_msg = "This example only supports instruments with demodulators."
        (daq, device, props) = zhinst.utils.create_api_session(
            device_id, apilevel_example, required_devtype=".*LI|.*IA|.*IS", required_err_msg=err_msg
        )
        zhinst.utils.api_server_version_check(daq)
        return (daq,device,props)
    except(RuntimeError):
        print('没有连接设备')


##实现参数栏中auxout和dmodR的实时刷新
def refresh_params_bar(x,daq,device,checkvar,bar_var,path):
        t=th.Thread(target=refresh_params_bar_thread,args=(daq,device,checkvar,bar_var,path))
        t.setDaemon(True)
        t.start()
def refresh_params_bar_thread(daq,device,checkvar,entry_str,path):
    #x是接受鼠标单击命令，无特殊含义
    #等待1秒是等checkvar更新
    if path=="/dev4346/demods/0/sample":
        print('dmodr')
        time.sleep(0.5)
        while checkvar.get() == 1:
            time.sleep(0.1)
            sigin = daq.getSample("/%s/demods/%d/sample" % (device, 0))
            r = np.abs(sigin['x'][0] + 1j * sigin['y'][0])
            entry_str.set(r)
    if path=="/dev4346/auxouts/0/value":
        print('aux')
        time.sleep(0.5)
        while checkvar.get()==1:
            time.sleep(0.2)
            au = daq.get("/dev4346/auxouts/0/value")
            aux = au['dev4346']['auxouts']['0']['value']['value'][0]
            entry_str.set(aux)

#画图  canvas,aix1,aix2,700,1300,frequency,R,frequency,phi
def plot_fig_sweep(canvas,aix1,aix2,*other):    #画图的窗口，图的数量，坐标参数（按照x1,y1,x2,y2等依次排列）
    #x_demo = np.linspace(0,6.282)
    #y_demo = np.sin(x_demo)

    #开始画
    aix1.clear()
    aix2.clear()
    aix1.plot(other[0],other[1])
    aix2.plot(other[2],other[3])
    canvas.draw()

def plot_fig_scan(canvas,fig,aix11,aix22,lst,x,y,x_lenth,y_lenth):

    #aix11.clear()
    #aix22.clear()

    fig.clear()
    aix1 = fig.add_subplot(121)
    aix2 = fig.add_subplot(122)

    pic1=aix1.imshow(lst,cmap='copper',origin='lower',extent=(0,x_lenth,0,y_lenth))
    aix1.set_title('total lenth:{}um'.format(x_lenth))
    aix2.set_title('total lenth:{}um'.format(x_lenth))
    #对x轴的数据进行改变
    x1 = np.linspace(0,x_lenth,len(x))
    aix2.plot(x1,y)
#colorbar
    fig.colorbar(pic1, ax=aix1, shrink=0.7)
    canvas.draw()


def plot_fig_in_files(listbox,canvas,fig,pathh):
    fig.clear()
    path=pathh+'/'+listbox.get(listbox.curselection())
    ##获得数据列表
    lst=np.load(path,allow_pickle=True)
    aix=fig.add_subplot(111)

    name = listbox.get(listbox.curselection())
    res = re.split('\+', name)

    if len(res)>3:
        x_lenth = eval(res[1])
        aix.set_title('total lenth:{}um'.format(x_lenth))
        pic1 = aix.imshow(lst, cmap='copper', origin='lower', extent=(0, x_lenth, 0, x_lenth))
        fig.colorbar(pic1, ax=aix, shrink=0.7)

    canvas.draw()

#高斯拟合sweep得到Q值
def q_calculate(x,y):
    #减去y的背景值
    background=y[0]
    y[:]=[i-background for i in y]
    #找出中心频率以及最大的y
    center = x[y.index(max(y))]
    peak = max(y)
    half_peak_left=0
    half_peak_right=1
#用每个点与半峰高的值的误差来找出最接近半峰高的点
    erro = [np.abs(i-peak/2) for i in y]
    half_peak_left = x[erro.index(min(erro[0:y.index(max(y))]))]
    half_peak_right = x[erro.index(min(erro[y.index(max(y)):]))]
    q=center/(half_peak_right-half_peak_left)
    return(q)
#扫频相关



def sweep(sf,st,samplec,canvas,aix1,aix2,Q,progress_f,daq,device,props):

    zhinst.utils.api_server_version_check(daq)
    #zhinst.utils.disable_everything(daq, device)
    out_channel = 0
    out_mixer_channel = zhinst.utils.default_output_mixer_channel(props)
    in_channel = 0
    demod_index = 0
    osc_index = 0 ##
    demod_rate = 10e3
    time_constant = 0.01
    exp_setting = [
        ["/%s/sigins/%d/ac" % (device, in_channel), 1],
        ["/%s/sigins/%d/autorange" % (device, in_channel), 1],
        ["/%s/demods/%d/enable" % (device, demod_index), 1],
        ["/%s/demods/%d/rate" % (device, demod_index), demod_rate],
        ["/%s/sigouts/%d/on" % (device, out_channel), 1],
        ["/%s/sigouts/%d/enables/%d" % (device, out_channel, out_mixer_channel), 1],
        ["/%s/sigouts/%d/range" % (device, out_channel), 0.01],
        ["/%s/sigouts/%d/amplitudes/%d" % (device, out_channel, out_mixer_channel), 0.005],
        ['/%s/demods/0/adcselect'%(device),0]
    ]
    daq.set(exp_setting)

    daq.sync()
    sweeper = daq.sweep()

    sweeper.set("device", device)
    # Specify the `gridnode`: The instrument node that we will sweep, the device
    # setting corresponding to this node path will be changed by the sweeper.
    sweeper.set("gridnode", "oscs/%d/freq" % osc_index)
    # Set the `start` and `stop` values of the gridnode value interval we will use in the sweep.
    sweeper.set("start", eval(sf))##

    sweeper.set("stop", eval(st))##
    # Set the number of points to use for the sweep, the number of gridnode
    # setting values will use in the interval (`start`, `stop`).
    samplecount = samplec
    sweeper.set("samplecount", int(eval(samplecount)))####
    # Specify logarithmic spacing for the values in the sweep interval.
    sweeper.set("xmapping", 0)
    # Automatically control the demodulator bandwidth/time constants used.
    # 0=manual, 1=fixed, 2=auto
    # Note: to use manual and fixed, bandwidth has to be set to a value > 0.
    #sweeper.set("bandwidthcontrol", 2)
    # Sets the bandwidth overlap mode (default 0). If enabled, the bandwidth of
    # a sweep point may overlap with the frequency of neighboring sweep
    # points. The effective bandwidth is only limited by the maximal bandwidth
    # setting and omega suppression. As a result, the bandwidth is independent
    # of the number of sweep points. For frequency response analysis bandwidth
    # overlap should be enabled to achieve maximal sweep speed (default: 0). 0 =
    # Disable, 1 = Enable.
    sweeper.set("bandwidthoverlap", 0)

    # Sequential scanning mode (as opposed to binary or bidirectional).
    sweeper.set("scan", 0)
    # Specify the number of sweeps to perform back-to-back.
    loopcount = 1#######
    sweeper.set("loopcount", loopcount)
    sweeper.set("settling/time", 0)

    sweeper.set("settling/inaccuracy", 0.001)

    sweeper.set("averaging/tc", 1)

    sweeper.set("averaging/sample", 2)
    sweeper.set('bandwidth',50)


##扫描输入信号
    path = "/%s/demods/%d/sample" % (device, demod_index)
    sweeper.subscribe(path)

    # Start the Sweeper's thread.
    sweeper.execute()

    start = time.time()
    timeout = 200  # [s]
    print("Will perform", loopcount, "sweeps...")

    while not sweeper.finished():  # Wait until the sweep is complete, with timeout.
        time.sleep(0.2)
        progress = sweeper.progress()
        print(progress[0],type(progress[0]))
        #刷新显示框
        progress_f.delete(0, tk.END)
        progress_f.insert(0, str(progress[0]))
        progress_f.update()
        time.sleep(0.2)
        #progress_f.insert(0,2)
        # Here we could read intermediate data via:
        # data = sweeper.read(True)...
        # and process it while the sweep is completing.
        # if device in data:
        # ...
        if (time.time() - start) > timeout:
            # If for some reason the sweep is blocking, force the end of the
            # measurement.
            print("\nSweep still not finished, forcing finish...")
            sweeper.finish()
    print("")

    # Read the sweep data. This command can also be executed whilst sweeping
    # (before finished() is True), in this case sweep data up to that time point
    # is returned. It's still necessary still need to issue read() at the end to
    # fetch the rest.
    return_flat_dict = True
    data = sweeper.read(return_flat_dict)
    sweeper.unsubscribe(path)

    # Check the dictionary returned is non-empty.
    assert data, "read() returned an empty data dictionary, did you subscribe to any paths?"
    # Note: data could be empty if no data arrived, e.g., if the demods were
    # disabled or had rate 0.
    assert path in data, "No sweep data in data dictionary: it has no key '%s'" % path
    samples = data[path]
    #print(samples)
    print("Returned sweeper data contains", len(samples), "sweeps.")
    assert len(samples) == loopcount, "The sweeper returned an unexpected number of sweeps: `%d`. Expected: `%d`." % (
        len(samples),
        loopcount,
    )

    for sample in samples:
        frequency = sample[0]["frequency"]
        R = np.abs(sample[0]["x"] + 1j * sample[0]["y"])
        R=R.tolist()
        frequency=frequency.tolist()
        phi = np.angle(sample[0]["x"] + 1j * sample[0]["y"])
        plot_fig_sweep(canvas,aix1,aix2,frequency,R,frequency,phi)

        lst=[frequency,R]
        np.savetxt(r'E:\pycharm\AFM\data\sweep_{}.txt'.format(time.strftime('%h_%e_%H_%M')), lst)
        print(R)
        print(frequency)
        print('maxsigin {}'.format(max(R)))
        max_r=max(R)
        q_value=q_calculate(frequency,R)
        Q.delete(0,tk.END)
        Q.insert(0,q_value)
    print('q{}'.format(q_value))
    #共振频率
    h=frequency[R.index(max(R))]
    print('共振频率为{}'.format(h))
   # ["/%s/sigins/%d/ac" % (device, in_channel), 1]
    daq.set([["/%s/oscs/%d/freq" %(device,0), h]])
    print("fre{},r{}".format(frequency,R))

    return h,max_r,q_value



#从设备加载config参数
def load_config_setting_fd(daq,device,current_range,current_scaling,
                           output_range,output_offset,output_freq,filter_bw,filter_order,filter_harmonic):
    current_range.delete(0,tk.END)
    current_scaling.delete(0,tk.END)
    output_range.delete(0,tk.END)
    output_offset.delete(0,tk.END)
    output_freq.delete(0,tk.END)
    filter_bw.delete(0,tk.END)
    filter_order.delete(0,tk.END)
    filter_harmonic.delete(0,tk.END)
    current_range.insert(0,daq.get("/%s/CURRINS/%d/RANGE" %(device,0)))
    ###current_scaling.insert(0,daq.get("" %(device,0)))
    current_scaling.insert(0, daq.get("/%s/CURRINS/%d/SCALING" % (device, 0)))
    output_range.insert(0, daq.get("/%s/SIGOUTS/%d/RANGE" % (device, 0)))
    output_offset.insert(0, daq.get("/%s/SIGOUTS/%d/OFFSET" % (device, 0)))
    output_freq.insert(0, daq.get("/%s/OSCS/%d/FREQ" % (device, 0)))
    filter_bw.insert(0, 1/np.pi/2/daq.get("/%s/DEMODS/%d/TIMECONSTANT" % (device, 0)))
    filter_order.insert(0, daq.get("/%s/DEMODS/%d/ORDER" % (device, 0)))
    filter_harmonic.insert(0, daq.get("/%s/DEMODS/%d/HARMONIC" % (device, 0)))
    pass


##advisor计算
def advise(daq,device,target_bw,gain,p_entry,i_entry,q,harm_freq,bw_label,pm_label):
    apilevel_example = 6  # The API level supported by this example.

    zhinst.utils.api_server_version_check(daq)

 #   daq.set([["/%s/pids/%d/demod/timeconstant" % (device, pid_index),tc ]])

    daq.sync()

    daq.set([[ '/%s/pids/0/mode'%(device), 0],
             ['/%s/pids/0/input'%(device), 2],
             ['/%s/pids/0/inputchannel'%(device), 0],
             ['/%s/pids/0/output'%(device), 5],
             ['/%s/pids/0/outputchannel'%(device), 0],
             ['/%s/pids/0/center'%(device), 4.5],
             ['/dev4346/pids/0/limitlower', -4.5],
             ['/dev4346/pids/0/limitupper', 4.5]])
    pid_index = 0  # PID index.

    pidAdvisor = daq.pidAdvisor()

    pidAdvisor.set("device", device)
    # Turn off auto-calc on param change. Enabled
    # auto calculation can be used to automatically
    # update response data based on user input.
    pidAdvisor.set("auto", False)
    pidAdvisor.set("pid/targetbw", target_bw)

    #PI
    pidAdvisor.set("pid/mode", 3)

    # PID index to use (first PID of device: 0)
    pidAdvisor.set("index", pid_index)

    # source = 6: Resonator amplitude
    pidAdvisor.set("dut/source", 6)
    pidAdvisor.set('dut/fcenter',harm_freq)
    print('harm_freq{}'.format(harm_freq))

#gain,q
    pidAdvisor.set('dut/gain', gain)
    pidAdvisor.set('dut/q',q)
    print('q_value{}'.format(q))


    pidAdvisor.set("pid/p", 0)
    pidAdvisor.set("pid/i", 0)
    pidAdvisor.set("pid/d", 0)

    # Start the module thread
    pidAdvisor.execute()

    # Advise
    pidAdvisor.set("calculate", 1)
    print("Starting advising. Optimization process may run up to a minute...")
    calculate = 1

    t_start = time.time()
    t_timeout = t_start + 90
    while calculate == 1:
        time.sleep(0.1)
        calculate = pidAdvisor.getInt("calculate")
        progress = pidAdvisor.progress()
        print(f"Advisor progress: {progress[0]:.2%}.", end="\r")
        if time.time() > t_timeout:
            pidAdvisor.finish()
            raise Exception("PID advising failed due to timeout.")
    print("")
    print(f"Advice took {time.time() - t_start:0.1f} s.")
    pidAdvisor.set( 'todevice',1)
    # Get all calculated parameters.
    result = pidAdvisor.get("*", True)
    assert result, "pidAdvisor returned an empty data dictionary?"

    if result is not None:
        # Now copy the values from the PID Advisor to the device's PID.
        pidAdvisor.set("todevice", 1)
        # Let's have a look at the optimised gain parameters.
        p_advisor = result["/pid/p"][0]
        i_advisor = result["/pid/i"][0]
        d_advisor = result["/pid/d"][0]

        bw = result['/targetfail'][0]
        pm = result['/stable'][0]
        f_0 = lambda a:'yes' if a==0 else 'no'
        f_1 = lambda a:'yes' if a==1 else 'no'
        #bw=f_0(bw)
        #pm=f_1(pm)
        print('BW:{},PM:{}'.format(bw,pm))
        p_entry.delete(0,tk.END)
        p_entry.insert(0,p_advisor)
        i_entry.delete(0, tk.END)
        i_entry.insert(0, i_advisor)
##更新bw,pm
        if bw==0:
            bw_label.config(bg='light green')
        else:
            bw_label.config(bg='red')
        bw_label.update()
        if pm==1:
            pm_label.config(bg='light green')
        else:
            bw_label.config(bg='red')
        pm_label.update()



##pid的打开与关闭
def pid_enable_disable(daq,device,props,max_sigin,state_var,setpoint_percent,button):
    apilevel_example = 6  # The API level supported by this example.
    err_msg = (
        "This example requires a UHF or an MF with the PID Option installed. "
        "For HF2, see the example zhinst.examples.hf2.example_pid_advisor_pll."
    )
    required_devtype = r"UHF|MF"  # Regular expression of supported instruments.

    pid_index = 0  # PID index.
    ##输入信号的峰值
    sigin = daq.getSample("/%s/demods/%d/sample" % (device, 0))
    max_sigin = np.abs(sigin['x'][0]+1j*sigin['y'][0])

    setpoint = setpoint_percent*max_sigin
    phase_unwrap = False

    out_channel = 0
    osc_index = 1
    # Get the value of the instrument's default Signal Output mixer channel.
    out_mixer_channel = zhinst.utils.default_output_mixer_channel(props)
    amplitude = 0.005
    if state_var.get()==0:
        time.sleep(1)
        state_var.set(1)
        button.config(text='disable',bg='red')
        exp_setting = [

        ["/%s/sigouts/%d/on" % (device, out_channel), 1],
        ["/%s/sigouts/%d/enables/%d" % (device, out_channel, out_mixer_channel), True],
        ["/%s/sigouts/%d/range" % (device, out_channel), 0.01],
        ["/%s/sigouts/%d/amplitudes/%d" % (device, out_channel, out_mixer_channel), amplitude],
        ["/%s/pids/%d/setpoint" % (device, pid_index), setpoint],
        ["/%s/pids/%d/enable" % (device, pid_index), True],
        ["/%s/pids/%d/phaseunwrap" % (device, pid_index), phase_unwrap],
        ["/%s/pids/%d/keepint" % (device, pid_index), 1]

        ]
        daq.set(exp_setting)


    else:
        state_var.set(0)
        button.config(text='enable',bg='light green')
        daq.set([["/%s/pids/%d/enable" % (device, pid_index), False]])

##pid的p,i,d能够实时改动
def change_pid_para(p_value,i_value,daq,device):
    t=th.Thread(target=change_pid_para_thread,args=(p_value,i_value,daq,device))
    t.isDaemon(True)
    t.start()

def change_pid_para_thread(p_value,i_value,daq,device):
    daq.set(["%s/PIDS/0/p" % (device), p_value])
    daq.set(["%s/PIDS/0/i" % (device), i_value])


###进针相关函数
##进针
def approach_thread(max_currentin,dev,daq,canvas,aix1,begin_stop_var,setpoint_p,plot_fig_var):
    ## 1表示在进针，图像会更新，0表示退针，图像会停止刷新

    #进针的线程
    t1=th.Thread(target=approach,args=(max_currentin,dev,daq,setpoint_p))
    t1.setDaemon(True)
    t1.start()

    ##设置一个线程来显示current_in，来判断进针状况，每过一定时间刷新图像,一直运行，直到程序关闭
    if begin_stop_var.get()==0:
        begin_stop_var.set(1)
        t2 = th.Thread(target=refresh_approach_fig, args=(dev, daq,canvas,aix1, begin_stop_var))
        t2.setDaemon(True)
        t2.start()
    pass
def approach(max_currentin,dev,daq,setpoint_p):

    setpoint=daq.get('/%s/PIDS/%d/SETPOINT'%(dev,0))
    setpointt=setpoint['dev4346']['pids']['0']['setpoint']['value'][0]
    max_currentin=setpointt/setpoint_p
    ##设置步进电机
    DeviceManagerCLI.BuildDeviceList()
    serialNo = DeviceManagerCLI.GetDeviceList(KCubeDCServo.DevicePrefix)
    print(serialNo)
    serialNo = '27252847'
    device = KCubeDCServo.CreateKCubeDCServo(serialNo)
    print(device)

    device.Connect(serialNo)
    device.WaitForSettingsInitialized(10000)
    motorconfiguration = device.LoadMotorConfiguration(serialNo)
    # motorconfiguration = device.LoadMotorConfiguration(serialNo,DeviceConfiguration.DeviceSettingsUseOptionType.UseFileSettings)

    motorconfiguration.DeviceSettingsName = 'Z812B'
    # motorconfiguration.DeviceSettingsName = 'MTS50/M-Z8'
    motorconfiguration.UpdateCurrentConfiguration()

    motorDeviceSettings = device.MotorDeviceSettings
    device.SetSettings(motorDeviceSettings, False)

    device.StartPolling(250)
    device.EnableDevice()
    currentin=max_currentin
    daq.set([["/%s/pids/%d/enable" % (dev, 0), True]])
    time.sleep(2)

    #步进的步数
    count=0
    while currentin>=max_currentin*0.98:
        device.MoveRelative(MotorDirection.Forward,System.Decimal(0.0002),60000)
        time.sleep(0.5)
        data=daq.getSample("/%s/demods/%d/sample" % (dev, 0))
        currentin=np.abs(data['x'][0]+1j*data['y'][0])
        print(currentin)
        print(count)
        count=1+count
    print('sigin突变')
    count = 0
    while np.abs(currentin-max_currentin*0.95)/(max_currentin*0.95)>0.002:
        device.MoveRelative(MotorDirection.Forward, System.Decimal(0.00015), 60000)
        time.sleep(0.5)
        data = daq.getSample("/%s/demods/%d/sample" % (dev, 0))
        currentin = np.abs(data['x'][0] + 1j * data['y'][0])
        print(currentin)
        print(count)
        count = 1 + count
    print('到达setpoint')
    count = 0
    aux=daq.get('/%s/auxouts/%d/value'%(dev,0))
    auxout_value=aux['dev4346']['auxouts']['0']['value']['value'][0]
    while np.abs(auxout_value-4.5)>0.1:
        device.MoveRelative(MotorDirection.Forward, System.Decimal(0.00009), 60000)
        time.sleep(0.5)
        aux = daq.get('/%s/auxouts/%d/value' % (dev, 0))
        auxout_value=aux['dev4346']['auxouts']['0']['value']['value'][0]
        print(auxout_value)
        print(count)
        count = 1 + count
    print('进针成功，辅助输出值为：{}'.format(auxout_value))
    device.StopPolling()
    device.ShutDown()
##刷新进针时的currentin图像
def refresh_approach_fig(dev,daq,canvas,aix1,begin_stop_var):

    x=np.linspace(0,99,100)
    y=np.linspace(0,0,100)

    while(begin_stop_var.get()==1):

        time.sleep(0.2)
        sample=daq.getSample("/%s/demods/%d/sample" % (dev, 0))

        for i in range(99):
            y[i]=y[i+1]
        y[99]=np.abs(sample['x'][0]+1j*sample['y'][0])
        aix1.clear()
        aix1.plot(x,y)
        canvas.draw()

##快速退针

def fast_quit():
    DeviceManagerCLI.BuildDeviceList()
    serialNo = DeviceManagerCLI.GetDeviceList(KCubeDCServo.DevicePrefix)
    print(serialNo)
    serialNo = '27252847'
    device = KCubeDCServo.CreateKCubeDCServo(serialNo)
    print(device)
    device.Connect(serialNo)
    device.WaitForSettingsInitialized(10000)
    motorconfiguration = device.LoadMotorConfiguration(serialNo)
    # motorconfiguration = device.LoadMotorConfiguration(serialNo,DeviceConfiguration.DeviceSettingsUseOptionType.UseFileSettings)

    motorconfiguration.DeviceSettingsName = 'Z812B'
    # motorconfiguration.DeviceSettingsName = 'MTS50/M-Z8'
    motorconfiguration.UpdateCurrentConfiguration()

    motorDeviceSettings = device.MotorDeviceSettings
    device.SetSettings(motorDeviceSettings, False)

    device.StartPolling(250)
    device.EnableDevice()
    device.MoveRelative(MotorDirection.Backward, System.Decimal(0.0005), 60000)
    time.sleep(1)
    device.StopPolling()
    device.ShutDown()
##退针
def quit_approach(dev,daq,begin_stop_var):
    begin_stop_var.set(0)
    #关闭pid，将mcl的x,y,z方向归零
    try:
        daq.set([["/%s/pids/%d/enable" % (dev, 0), 0]])
    except:
        print("pid已关闭")
    time.sleep(1)
    dll = ctypes.windll.LoadLibrary(
        r'D:\edge_download\mcl\Program Files 64\Mad City Labs\AFM\Components\NanoDrive\Madlib.dll')

    handle = dll.MCL_InitHandle()
    for i in range(1,4):
        dll.MCL_SingleWriteN(ctypes.c_double(0), i, handle)
        time.sleep(1)
    dll.MCL_ReleaseHandle(handle)
    #将步进电机远离样品表面
    DeviceManagerCLI.BuildDeviceList()
    serialNo = DeviceManagerCLI.GetDeviceList(KCubeDCServo.DevicePrefix)
    print(serialNo)
    serialNo = '27252847'
    device = KCubeDCServo.CreateKCubeDCServo(serialNo)
    print(device)
    device.Connect(serialNo)
    device.WaitForSettingsInitialized(10000)
    motorconfiguration = device.LoadMotorConfiguration(serialNo)
    # motorconfiguration = device.LoadMotorConfiguration(serialNo,DeviceConfiguration.DeviceSettingsUseOptionType.UseFileSettings)

    motorconfiguration.DeviceSettingsName = 'Z812B'
    # motorconfiguration.DeviceSettingsName = 'MTS50/M-Z8'
    motorconfiguration.UpdateCurrentConfiguration()

    motorDeviceSettings = device.MotorDeviceSettings
    device.SetSettings(motorDeviceSettings, False)

    device.StartPolling(250)
    device.EnableDevice()
    try:
        device.Home(60000)
    except:
        print('步进电机home失败')
    try:
        device.StopPolling()
        device.ShutDown()
    except:
        print("步进电机断开连接失败")
    print('退针成功')

##扫描相关函数
def scan_thread(canvas,fig,aix1,aix2,x_points,x_lenth,y_points,y_lenth,time_per_point,direction,begin_or_stop,daq,x_start,y_start,begin_button):
    x_unit = x_lenth / x_points
    y_unit = y_lenth / y_points
    ###x_points与y_points相等
    data=[[2.5 for i in range(x_points)]for j in range(y_points)]
    data=np.array(data)
    data_reverse = np.zeros((x_points, y_points))  # 将直接读取到的数据用最高点的数据减去每个数据得到实际形貌
    data_auxout=np.zeros((x_points, y_points))
    dll = ctypes.windll.LoadLibrary(
        r'D:\edge_download\mcl\Program Files 64\Mad City Labs\AFM\Components\NanoDrive\Madlib.dll')

    handle = dll.MCL_InitHandle()
    print('handle',handle)
    # dll.MCL_SingleWriteZ(ctypes.c_double(0), handle)
    # print(dll.MCL_SingleReadN(1, handle))
    # print(dll.MCL_MonitorN(ctypes.c_double(0), 3, handle)))
    dll.MCL_SingleReadN.restype = ctypes.c_double
    dll.MCL_SingleReadZ.restype = ctypes.c_double
    ##两个个用来统计平均值的变量
    sum_ = 0
    average_height = 0
    if direction == 'along the x-axis':
        for y in range(y_points):
            dll.MCL_SingleWriteN(ctypes.c_double(y_start+y * y_unit), 2, handle)
            time.sleep(1)

            ##扫描
            for x in range(x_points):
                if begin_or_stop.get() == 0:  ##暂停扫描
                    np.save(r'D:\pycharm\Afm\data\{}+{}+{}+.npy'.format(time.strftime('%h_%e_%H_%M'),x_lenth,y_lenth), data)
                    np.save(r'D:\pycharm\Afm\data\z_position_reverse {}+{}+{}+.npy'.format(time.strftime('%h_%e_%H_%M'),x_lenth,y_lenth),data_reverse)
                    dll.MCL_ReleaseHandle(handle)
                    return 0
                dll.MCL_SingleWriteN(ctypes.c_double(x_start+x * x_unit), 1, handle)
                time.sleep(time_per_point)
                ##采集数据
                data[x][y] =dll.MCL_SingleReadZ(handle)
                print(data[x][y])
                '''height=0
                for i in range(5):
                    height+= dll.MCL_SingleReadZ( handle)
                    time.sleep(0.003)
                data[x][y] = height / 5
                print(data[x][y],height)'''
            if y<x_points/3:
                sum_=sum_+sum(data[:,y])
                average_height=sum_/(y+1)/x_points
                for y1 in range(y+1,y_points):
                    for x1 in range(x_points):
                        data[x1][y1]=average_height
            plot_fig_scan(canvas,fig,aix1,aix2, data, range(x_points), data[:,y],x_lenth,y_lenth)
            ##回针
            for count in range(30):
                dll.MCL_SingleWriteN(ctypes.c_double(x_start + x_lenth * (1 - count / 30)), 1, handle)
                time.sleep(0.1)

    else:
        for x in range(x_points):

            dll.MCL_SingleWriteN(ctypes.c_double(x_start+x * x_unit), 1, handle)
            time.sleep(1)
            for y in range(y_points):
                if begin_or_stop.get() == 0:  ##暂停扫描
                    np.save(r'D:\pycharm\Afm\data\{}+{}+{}+.npy'.format(time.strftime('%h_%e_%H_%M'), x_lenth,y_lenth), data)
                    np.save(r'D:\pycharm\Afm\data\z_position_reverse {}+{}+{}+.npy'.format(time.strftime('%h_%e_%H_%M'),x_lenth,y_lenth),data_reverse)
                    dll.MCL_ReleaseHandle(handle)
                    return 0

                dll.MCL_SingleWriteN(ctypes.c_double(y_start+y * y_unit), 2, handle)
                time.sleep(time_per_point)

                #auxout data
                au = daq.get("/dev4346/auxouts/0/value")
                aux = au['dev4346']['auxouts']['0']['value']['value'][0]
                #采集数据
                data[x][y] = dll.MCL_SingleReadZ(handle)
                print(data[x][y])
                '''height2 = 0
                for i in range(5):
                    height2 += dll.MCL_SingleReadN(3, handle)
                    time.sleep(0.003)
                data[x][y] = height2 / 5
                print(data[x][y],height2)'''
            if x < x_points /3:
                sum_ = sum_ + sum(data[x,:])
                average_height = sum_ / (x+ 1) / x_points
                for x1 in range(x + 1, y_points):
                    for y1 in range(x_points):
                        data[x1][y1] = average_height
            plot_fig_scan(canvas,fig,aix1,aix2, data, range(x_points), data[x,:],x_lenth,y_lenth)
            ##回针
            for count in range(30):
                dll.MCL_SingleWriteN(ctypes.c_double(y_start + y_lenth * (1 - count / 30)), 2, handle)
                time.sleep(0.1)

    peak_point = np.max(data)
    for i in range(x_points):
        for j in range(y_points):
            data_reverse[i][j] = peak_point - data[i][j]
    plot_fig_scan(canvas,fig,aix1,aix2, data_reverse, range(x_points), data[x],x_lenth,y_lenth)
    np.save(r'D:\pycharm\Afm\data\z_position {}+{}+{}+.npy'.format(time.strftime('%h_%e_%H_%M'),x_lenth,y_lenth), data)
    np.save(r'D:\pycharm\Afm\data\z_position_reverse {}+{}+{}+.npy'.format(time.strftime('%h_%e_%H_%M'),x_lenth,y_lenth), data_reverse)
    np.savetxt(r'D:\pycharm\Afm\data\z_position {}+{}+{}+.txt'.format(time.strftime('%h_%e_%H_%M'),x_lenth,y_lenth), data)
    np.savetxt(r'D:\pycharm\Afm\data\z_position_reverse {}+{}+{}+.txt'.format(time.strftime('%h_%e_%H_%M'),x_lenth,y_lenth), data_reverse)
    np.savetxt(r'D:\pycharm\Afm\data\auxout_{}+{}+{}+.txt'.format(time.strftime('%h_%e_%H_%M'), x_lenth,y_lenth),data_auxout)
    dll.MCL_ReleaseHandle(handle)
    begin_or_stop.set(0)
    begin_button.config(text='begin')
def scan_control(canvas,fig,aix1,aix2,x_points,x_lenth,y_points,y_lenth,time_per_point,direction,begin_or_stop,begin_button,daq,x_start,y_start):
    ##0表示关闭，1表示正在运行
    if begin_or_stop.get()==0:
        begin_button.config(text='stop')
        begin_or_stop.set(1)
        begin_button.update()
        t=th.Thread(target=scan_thread,args=(canvas,fig,aix1,aix2,x_points,x_lenth,y_points,y_lenth,time_per_point,direction,begin_or_stop,daq,x_start,y_start,begin_button))
        t.setDaemon(True)
        t.start()

    else:
        begin_or_stop.set(0)
        begin_button.config(text='begin')
        begin_button.update()


#位移台位置归零

def set_zero(para):

    dll = ctypes.windll.LoadLibrary(
        r'D:\edge_download\mcl\Program Files 64\Mad City Labs\AFM\Components\NanoDrive\Madlib.dll')

    handle = dll.MCL_InitHandle()
    if para=='x':
        dll.MCL_SingleWriteN(ctypes.c_double(0), 1, handle)
    elif para=='y':
        dll.MCL_SingleWriteN(ctypes.c_double(0), 2, handle)
    elif para=='xy':
        dll.MCL_SingleWriteN(ctypes.c_double(0), 1, handle)
        dll.MCL_SingleWriteN(ctypes.c_double(0), 2, handle)

    dic = {'x': lambda:dll.MCL_SingleWriteN(ctypes.c_double(0), 1,handle),
           'y': lambda:dll.MCL_SingleWriteN(ctypes.c_double(0), 2,handle),
           'z': lambda:dll.MCL_SingleWriteN(ctypes.c_double(0), 1,handle),
           'xy': lambda: dll.MCL_SingleWriteN(ctypes.c_double(0), i,handle)}

    dll.MCL_ReleaseHandle(handle)
##利用线程来处理listbox的选中状态
def list_box_thread(listbox,canvas,fig,path_var):
    pathh=re.sub(r'\\','/',path_var.get())
    t=th.Thread(target=plot_fig_in_files,args=(listbox,canvas,fig,pathh))
    t.setDaemon(True)
    t.start()

def refresh_file_lst(list_box,path):

    pathh=re.sub(r'\\','/',path)
    filelst = os.listdir(pathh)
    list_box.delete(0,tk.END)

    if len(filelst) != 0:
        for i in (filelst):
            list_box.insert(tk.END,i)








