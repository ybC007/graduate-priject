import tkinter as tk
import tkinter.messagebox as msb
from tkinter import ttk
import function
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.pyplot import Figure




class View():
    def __init__(self, root):
        self.parent = root
        self.init_windows()
        self.max_sigin=0.00114
        self.hamo_freq=33650
        self.q=694
        self.setpoint=0.95

    def init_windows(self):
        self.create_window()
        self.create_params_bar()
        self.create_taps()
        self.daq=0
        self.device=0
        self.device_props=0
        self.device_id='dev4346'
        try:
            self.daq,self.device,self.device_props=function.create_session(self.device_id)
        except(TypeError):
            print('设备没有返回daq,device,props')

    def create_window(self):
        self.menu_bar = tk.Menu(self.parent)
        self.parent.config(menu=self.menu_bar)
        self.file_menu = tk.Menu(self.parent, bd=2, tearoff=0)
        self.about_about_menu = tk.Menu(self.parent, bd=2, tearoff=0)
        self.help_menu = tk.Menu(self.parent, bd=2, tearoff=0)
        self.menu_bar.add_cascade(label='File', menu=self.file_menu)
        self.menu_bar.add_cascade(label='About', menu=self.about_about_menu)
        self.menu_bar.add_cascade(label='Help', menu=self.help_menu)

        self.file_menu.add_command(label='Exit', command=self.quit)
        self.help_menu.add_command(label='Help', command=self.help)
        self.about_about_menu.add_command(label='About', command=self.about)

    def quit(self):
        pass

    def help(self):
        msb.showinfo('Help', 'Temporarily no info')

    def about(self):
        msb.showinfo('About the software', 'This is a software for afm')
        pass
    ##传递参数setpoint
    def pass_para(self,var):
        self.setpoint=var.get()

    def create_params_bar(self):  # PId
        self.params_bar = tk.Frame(self.parent, height=15, takefocus=0, pady=4)
        self.params_bar.pack(expand='no', fill='x', anchor='n')

        label_width = 12
        entry_width = 10
        #demodR实时显示
        dmodvar=tk.IntVar()
        dmod_checkb=tk.Checkbutton(self.params_bar,text='Dmod R',onvalue=1,offvalue=0,variable=dmodvar)
        dmod_checkb.grid(row=0,column=1)
        demod_entry_var = tk.StringVar()
        demod_entry = tk.Entry(self.params_bar,width=entry_width,textvariable=demod_entry_var)
        demod_entry.grid(row=0, column=2)
        dmod_checkb.bind(sequence='<Button-1>',func=lambda x:function.refresh_params_bar(x,self.daq,self.device,dmodvar,demod_entry_var,
                                                                                "/dev4346/demods/0/sample"))

        #aux输出实时显示
        auxvar=tk.IntVar()
        aux_checkb=tk.Checkbutton(self.params_bar,text='AUXOUT',onvalue=1,offvalue=0,variable=auxvar)
        aux_checkb.grid(row=0,column=3)
        aux_bar_var = tk.DoubleVar()
        aux_bar_var.set(1)
        scale_bar = tk.Scale(self.params_bar, variable=aux_bar_var, from_=0, to=9, orient=tk.HORIZONTAL, resolution=0.0001,
                              sliderlength=5,length=150,showvalue=False)
        scale_bar.grid(row=0,column=4)
        aux_checkb.bind(sequence='<Button-1>',func=lambda x:function.refresh_params_bar(x,self.daq,self.device,auxvar,aux_bar_var,
                                                                                        "/dev4346/auxouts/0/value"))
        #pid参数

        tk.Label(self.params_bar, text='Target BW', width=label_width).grid(row=0, column=8)
        target_bw_var=tk.DoubleVar()
        target_bw_var.set(10)
        target_bw_entry=tk.Entry(self.params_bar,width=entry_width,textvariable=target_bw_var)
        target_bw_entry.grid(row=0,column=9)

        tk.Label(self.params_bar, text='Gain', width=label_width).grid(row=0, column=10)
        gain_var=tk.DoubleVar()
        gain_entry=tk.Entry(self.params_bar,width=entry_width,textvariable=gain_var)
        gain_entry.grid(row=0,column=11)

        tk.Label(self.params_bar,text='setpoint', width=label_width).grid(row=0,column=12)
        setpoint_var=tk.DoubleVar()
        setpoint_var.set(0.95)
        setpoint_entry=tk.Entry(self.params_bar,width=entry_width,textvariable=setpoint_var)
        setpoint_entry.grid(row=0,column=13)
##修改setpoint
        setpoint_entry.bind(sequence='<Return>',func=lambda x: self.pass_para(setpoint_var))


        tk.Label(self.params_bar, text='P', width=int(label_width/3)).grid(row=0, column=14)
        p_var = tk.DoubleVar()
        p_entry = tk.Entry(self.params_bar, width=entry_width)
        p_entry.grid(row=0, column=15)

        tk.Label(self.params_bar, text='I', width=int(label_width/3)).grid(row=0, column=16)
        i_var = tk.DoubleVar()
        i_entry = tk.Entry(self.params_bar, width=entry_width)
        i_entry.grid(row=0, column=17)

        bw=tk.Label(self.params_bar, text='BW', width=int(label_width/3),bg='gray')
        bw.grid(row=0, column=18,padx=2)
        pm=tk.Label(self.params_bar, text='PM', width=int(label_width/3),bg='gray')
        pm.grid(row=0, column=19,padx=2)

        #advise
        advisor_button=tk.Button(self.params_bar, text='Advise',command=lambda :function.advise(self.daq,self.device,target_bw_var.get(),gain_var.get(),p_entry,i_entry,self.q,self.hamo_freq,bw,pm))
        advisor_button.grid(row=0,column=6,padx=2)
        ##enable or disable pid
        pid_state_var=tk.IntVar()
        pid_state_var.set(0)
        pid_enable_disen_button=tk.Button(self.params_bar,bg='light green',text='enable',command=lambda :function.pid_enable_disable(self.daq,self.device,self.device_props,self.max_sigin,pid_state_var,setpoint_var.get(),pid_enable_disen_button))
        pid_enable_disen_button.grid(row=0,column=7,padx=2)

        ##能够修改p,i并同步到设备
        self.params_bar.bind(sequence='<Button-1>',func=lambda x:function.change_pid_para(p_var.get(),i_var.get(),self.daq,self.device))


    def create_taps(self):
        ttk.Style().configure("Whte.TLabel", background="WhiteSmoke", pady=4)

        self.tab_control = ttk.Notebook(self.parent, style="Whte.TLabel")
        self.tab_sweeeper = tk.Frame(self.tab_control)
        self.tab_figure = tk.Frame(self.tab_control)
        self.tab_approach = tk.Frame(self.tab_control)
        self.tab_scan = tk.Frame(self.tab_control)

        self.tab_control.add(self.tab_sweeeper, text='  sweeper  ')
        self.tab_control.add(self.tab_approach, text='  approach  ')
        self.tab_control.add(self.tab_scan, text='  scan  ')
        self.tab_control.add(self.tab_figure, text='figure')
        self.tab_control.pack(expand='no', fill='x')


        self.sweeper_layout()
        self.figure_layout()
        self.approach_layout()
        self.scan_layout()



    def figure_layout(self):
        frame_files = tk.Frame(self.tab_figure, width=200, height=1080, bg='beige')
        frame_files.pack_propagate(0)
        frame_files.pack(side='left', expand='no', fill='y')
        frame_fig = tk.Frame(self.tab_figure, width=1700, height=1080)
        frame_fig.pack_propagate(0)
        frame_fig.pack(side='right', expand='yes', fill='both')

        '''path = r'E:\pycharm\AFM\data'
        filelst = os.listdir(path)'''

        tk.Label(frame_files,text='path',width=5,anchor='nw',relief='groove',padx=1).grid(row=0,column=1,sticky='w')
        path_var=tk.StringVar()
        path_var.set('D:\pycharm\Afm\data')
        path_entry=tk.Entry(frame_files,textvariable=path_var,width=20)
        path_entry.grid(row=0,column=2,columnspan=2,padx=1)

        #文件列表
        list_box = tk.Listbox(frame_files, selectmode='single', width=30)
        list_box.grid(row=1, column=1, columnspan=2, sticky='w')
        #滚动条
        #y滚动条
        scroll_bar_v = tk.Scrollbar(frame_files)
        scroll_bar_v.grid(row=1, column=3, sticky=tk.NS)
        scroll_bar_v.config(command=list_box.yview)
        list_box.config(yscrollcommand=scroll_bar_v.set)
        #x滚动条
        scroll_bar_h = tk.Scrollbar(frame_files,orient=tk.HORIZONTAL)
        scroll_bar_h.grid(row=2, column=1,columnspan=3, sticky=tk.EW)
        scroll_bar_h.config(command=list_box.xview)
        list_box.config(xscrollcommand=scroll_bar_h.set)

        #创建画布和轴
        fig = Figure(figsize=(5, 5), dpi=100)
        canvas = FigureCanvasTkAgg(figure=fig, master=frame_fig)

        canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
        canvas.draw()
        toobar = NavigationToolbar2Tk(canvas, frame_fig)
        toobar.update()

        ##刷新文件列表
        function.refresh_file_lst(list_box,path_var.get())
        ##绑定单击刷新文件列表
        frame_files.bind(sequence='<Button-1>',func=lambda x:function.refresh_file_lst(list_box,path_var.get()))
        ##绑定单击画图
        list_box.bind(sequence='<Button-1>', func=lambda x: function.list_box_thread(list_box, canvas,fig, path_var))



    def sweeper_layout(self):
        frame_param = tk.Frame(self.tab_sweeeper, bg='grey', width=200, height=1080)
        frame_param.pack(side='left', expand='no', fill='y')
        frame_figure = tk.Frame(self.tab_sweeeper, bg='beige', width=1000, height=1080, padx=4)
        frame_figure.pack(side='right',expand='yes', fill='both')
        #开始与结束的频率
        tk.Label(frame_param, text='sweep from', width=12, anchor='nw',relief='ridge',pady=1).grid(row=1, column=1,sticky='n')
        tk.Label(frame_param, text='sweep to', width=12, anchor='nw',relief='ridge',pady=1).grid(row=2, column=1,sticky='n')
        sweep_from = tk.StringVar()
        sweep_to = tk.StringVar()
        self.sf = tk.Entry(frame_param, textvariable=sweep_from,width=10)
        self.st = tk.Entry(frame_param, textvariable=sweep_to,width=10)
        self.sf.insert(0,33700)
        self.st.insert(0,33900)
        self.sf.grid(row=1, column=2)
        self.st.grid(row=2, column=2)
        #扫描点数
        tk.Label(frame_param, text='sample count', width=12, anchor='nw',relief='ridge',pady=1).grid(row=4, column=1,sticky='n')
        sample_num = tk.StringVar()
        sample_count = tk.Entry(frame_param, textvariable=sample_num,width=10)
        sample_count.insert(0,40)
        sample_count.grid(row=4, column=2)

        #进度
        tk.Label(frame_param,text='Progress',width=12,anchor='nw',relief='ridge',pady=1).grid(row=8,column=1,sticky='n')
        sweep_progress_str=tk.StringVar()
        sweep_progerss=tk.Entry(frame_param,width=10)
        sweep_progerss.grid(row=8,column=2)

        #Q值
        tk.Label(frame_param,text='Q',width=12,anchor='nw',relief='ridge',pady=1).grid(row=9,column=1,sticky='n')
        q_str=tk.StringVar()
        q=tk.Entry(frame_param,width=10,textvariable=q_str)
        q.grid(row=9,column=2)
        #共振频率
        tk.Label(frame_param,text='hamo_freq',width=12,anchor='nw',relief='ridge',pady=1).grid(row=10,column=1,sticky='n')
        hamo_freq_str=tk.DoubleVar()
        hamo_freq_entry=tk.Entry(frame_param,width=10,textvariable=hamo_freq_str)
        hamo_freq_entry.grid(row=10,column=2)
        #信号幅值
        tk.Label(frame_param, text='max_sigin', width=12, anchor='nw', relief='ridge', pady=1).grid(row=11, column=1,sticky='n')
        max_sigin_str=tk.DoubleVar()
        max_sigin_entry=tk.Entry(frame_param,width=10,textvariable=max_sigin_str)
        max_sigin_entry.grid(row=11,column=2)
        #开始
        tk.Button(frame_param, text='start', width=12,
                  command=lambda: self.start_sweep(self.sf.get(), self.st.get(),sample_count.get(),canvas,aix1,aix2,q,sweep_progerss,max_sigin_str,hamo_freq_str)).grid(
            row=12, column=1, sticky='w')

        ##绑定鼠标单击更新q,hamo_freq,max_sigin
        frame_param.bind(sequence='<Button-1>',func=lambda x:self.refresh_para_of_fre_q_sigin(eval(q_str.get()),hamo_freq_str.get(),max_sigin_str.get()))

        ##在frame_fig中创建画布和轴
        fig = Figure(figsize=(5, 5), dpi=100)
        canvas = FigureCanvasTkAgg(figure=fig, master=frame_figure)
        aix1 = fig.add_subplot(211)
        aix2 = fig.add_subplot(212)
        canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
        canvas.draw()
        toobar = NavigationToolbar2Tk(canvas,frame_figure)
        toobar.update()
        #测试
        list=[1,2,3,4,5,6]
        function.plot_fig_sweep(canvas,aix1,aix2,list,list,list,list)

    def start_sweep(self, sf, st,  samplecount,canvas,aix1,aix2,q,sweep_progress,max_sigin_str,hamo_freq_str):
        self.hamo_freq,self.max_sigin,self.q =function.sweep(sf, st,  samplecount, canvas,aix1,aix2,q,sweep_progress,self.daq,self.device,self.device_props)
        max_sigin_str.set(self.max_sigin)
        print(max_sigin_str.get())
        hamo_freq_str.set(self.hamo_freq)
###可以在sweep中设置q,共振频率，max_sigin
    def refresh_para_of_fre_q_sigin(self,q,hamo_freq,max_sigin):
        self.q=q
        self.hamo_freq=hamo_freq
        self.max_sigin=max_sigin
        self.daq.set([["/%s/oscs/%d/freq" %(self.device,0), hamo_freq]])
        print('q:{},freq:{},sigin:{}'.format(self.q,self.hamo_freq,self.max_sigin))



    def approach_layout(self):

        begin_stop_var=tk.IntVar()
        begin_stop_var.set(0)

        frame_param = tk.Frame(self.tab_approach, bg='grey', width=500, height=1080)
        frame_param.pack(side='left', fill='y', expand='no')
        frame_figure = tk.Frame(self.tab_approach, bg='beige', width=1400, height=1080, padx=4)
        frame_figure.pack(expand='yes', fill='both')
        #开始进针，快速退针，直接退出进针
        plot_fig_var=tk.IntVar()
        plot_fig_var.set(0)
        begin_button=tk.Button(frame_param,text='begin',width=10,command=lambda :function.approach_thread(self.max_sigin,self.device,self.daq,canvas,aix1,begin_stop_var,self.setpoint,plot_fig_var))
        begin_button.grid(row=1,column=1)
        fast_quit_button = tk.Button(frame_param,text='fast_q/100nm',width=10,command = lambda :function.fast_quit())
        fast_quit_button.grid(row=2,column=1)
        quit_button=tk.Button(frame_param,text='quit',width=10,command=lambda :function.quit_approach(self.device,self.daq,begin_stop_var))
        quit_button.grid(row=3,column=1)

        ##创建画布和轴
        fig = Figure(figsize=(5, 5), dpi=100)
        canvas = FigureCanvasTkAgg(figure=fig, master=frame_figure)
        aix1 = fig.add_subplot(111)
        canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
        canvas.draw()
        toobar = NavigationToolbar2Tk(canvas, frame_figure)
        toobar.update()
        ##测试
        list=[1,2,3,4,5]
        aix1.plot(list,list)


    def scan_layout(self):
        frame_param = tk.Frame(self.tab_scan, bg='grey', width=200, height=1080)
        frame_param.pack(side='left',expand='no',fill='y')
        frame_figure=tk.Frame(self.tab_scan,bg='ivory',width=1700,height=1080)
        frame_figure.pack(side='top',fill='both',expand='yes')
        #tk.Label(frame_param, text='sweep from', width=18, anchor='w').grid(row=1, column=1)

        tk.Label(frame_param,text='x_points',anchor='nw', width=10,relief='ridge').grid(row=1,column=1,sticky=tk.NW)
        tk.Label(frame_param, text='x_lenth/um',anchor='nw', width=10,relief='ridge').grid(row=2, column=1,sticky='n')
        tk.Label(frame_param, text='y_points',anchor='nw', width=10,relief='ridge').grid(row=3, column=1,sticky='n')
        tk.Label(frame_param, text='y_lenth/um',anchor='nw', width=10,relief='ridge').grid(row=4, column=1,sticky='n')

        tk.Label(frame_param, text='x_start/um',anchor='nw', width=10,relief='ridge').grid(row=5, column=1,sticky='n')
        tk.Label(frame_param, text='y_start/um', anchor='nw', width=10, relief='ridge').grid(row=6, column=1,sticky='n')

        tk.Label(frame_param,text='seconds/point',anchor='nw',width=10,relief='ridge').grid(row=50,column=1,sticky='n')
        tk.Label(frame_param,text='total time',anchor='nw',width=10,relief='ridge').grid(row=60,column=1,sticky='n')
        tk.Label(frame_param,text='direction',anchor='nw',width=10,relief='ridge').grid(row=70,column=1,sticky='n')

        x_points_str=tk.IntVar()
        x_lenth_str=tk.DoubleVar()
        y_points_str=tk.IntVar()
        y_lenth_str=tk.DoubleVar()
        x_start_var=tk.DoubleVar()
        y_start_var=tk.DoubleVar()
        time_stay_str = tk.DoubleVar()
        total_time_str=tk.StringVar()
        x_points_str.set(20)
        y_points_str.set(20)
        x_lenth_str.set(5)
        y_lenth_str.set(5)
        x_start_var.set(0.1)
        y_start_var.set(0.1)
        time_stay_str.set(0.3)
        ##每行回针时间为3秒
        ##总点数x每个点时间+每个点采样时间x点数+每行回针时间x行数
        total_time = (x_points_str.get()*y_points_str.get()*time_stay_str.get()+0.015*x_points_str.get()*y_points_str.get()+3*x_points_str.get())
        total_time_str.set('{}min{}s'.format(total_time//60,total_time%60))
        direction_str=tk.StringVar()

        # 创建画布和轴
        fig = Figure(figsize=(5, 5), dpi=100)
        canvas = FigureCanvasTkAgg(figure=fig, master=frame_figure)
        aix1 = fig.add_subplot(121)
        aix2 = fig.add_subplot(122)
        canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
        canvas.draw()
        toobar = NavigationToolbar2Tk(canvas, frame_figure)
        toobar.update()


        #绑定鼠标左键更新total_time
        frame_param.bind(sequence='<Button-1>',func= lambda x:total_time_str.set('{}min{}s'.format((x_points_str.get()*y_points_str.get()*time_stay_str.get()+x_points_str.get()+0.015*x_points_str.get()*y_points_str.get())//60,(x_points_str.get()*y_points_str.get()*time_stay_str.get()+x_points_str.get()+0.015*x_points_str.get()*y_points_str.get())%60)))

        x_points_entry=tk.Entry(frame_param,textvariable=x_points_str)
        x_points_entry.grid(row=1,column=2)
        x_lenth_entry=tk.Entry(frame_param,textvariable=x_lenth_str)
        x_lenth_entry.grid(row=2,column=2)
        y_points_entry=tk.Entry(frame_param,textvariable=y_points_str)
        y_points_entry.grid(row=3,column=2)
        y_lenth_entry=tk.Entry(frame_param,textvariable=y_lenth_str)
        y_lenth_entry.grid(row=4,column=2)
        x_start_entry=tk.Entry(frame_param,textvariable=x_start_var)
        x_start_entry.grid(row=5,column=2)
        y_start_entry = tk.Entry(frame_param, textvariable=y_start_var)
        y_start_entry.grid(row=6, column=2)
        time_stay_entry=tk.Entry(frame_param,textvariable=time_stay_str)
        time_stay_entry.grid(row=50,column=2)
        total_time_entry = tk.Entry(frame_param,textvariable=total_time_str)
        total_time_entry.grid(row=60,column=2)
        direction = tk.Spinbox(frame_param,values = ('along the x-axis','along the y-axis'),wrap=True,textvariable = direction_str,width=15)
        direction.grid(row=70,column=2,sticky='w')
        #创建一个变量来控制扫描的开始与暂停,1表示开始，0表示暂停
        begin_or_stop = tk.IntVar()
        begin_or_stop.set(0)
        begin_scan_button=tk.Button(frame_param,text='begin',width=10,command=lambda : function.scan_control(canvas,fig,aix1,aix2,x_points_str.get(),x_lenth_str.get()
                                                                                     ,y_points_str.get(),y_lenth_str.get(),time_stay_str.get(),direction_str.get(),begin_or_stop,begin_scan_button,self.daq,x_start_var.get(),y_start_var.get()))

        begin_scan_button.grid(row=80,column=1,sticky='w')

        #将位移台的位置归零
        set_zero_strvar=tk.StringVar()
        set_zero_spinbox=tk.Spinbox(frame_param,values=('x','y','x_y'),wrap=True,textvariable=set_zero_strvar,width=15)
        set_zero_spinbox.grid(row=90,column=2,sticky='w')

        set_zero=tk.Button(frame_param,text='set zero',width=10,command= lambda :function.set_zero(set_zero_strvar.get()))
        set_zero.grid(row=90,column=1,sticky='w')
        ##测试
        lst=np.load('data\z_position_reverse May_ 6_16_18+5.0+5.0+.npy',allow_pickle=True)
        x_demo = np.linspace(0,5,50)
        function.plot_fig_scan(canvas,fig,aix1,aix2,lst,x_demo,lst[:,10],6,6)



def main():
    root = tk.Tk()
    root.title('Afm')
    root.geometry('{}x{}+{}+{}'.format(root.winfo_screenwidth(),root.winfo_screenheight(),0,0))
    print(root.winfo_screenwidth(),root.winfo_screenheight())
    View(root)

    root.mainloop()


if __name__ == '__main__':
    main()
