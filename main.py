
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.core.window import Window, WindowBase
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.animation import Animation

import time
from time import strftime
import sqlite3
from sqlite3 import Error

#timestamp
tm= time.localtime()

#for databases
tmStmp=  "{}{}{}".format(tm.tm_mday,tm.tm_mon,tm.tm_year)

#popup class for the update part
class EditPop(Popup):
    pass

#popup class for the delete part
class DeletePop(Popup):
    pass

#MainScreen will have keys for previous and present activities
class MainScreen(Screen):
    pass

#PreviousScreen for past activities
class PreviousScreen(Screen):
    pass

#PresentScreen for current activities addition and changes
class PresentScreen(Screen):
    prod_name= ObjectProperty()
    tot_price= ObjectProperty()
    paid_price= ObjectProperty()

    rv= ObjectProperty()
    list_index= 0
    item_key= ''
    database_list=[]

    db= "database/db_{}.db".format(tmStmp)


    #submit new data into the existing list
    def submit(self):
        prd_name= self.prod_name.text
        price= self.tot_price.text
        paid= self.paid_price.text

        if (len(prd_name) and price and paid):

            self.prod_name.text=""
            self.tot_price.text=""
            self.paid_price.text=""

            #for each table item in the database
            tm= time.localtime()
            stmp= "{}{}{}".format(tm.tm_hour, tm.tm_min, tm.tm_sec)

            try:
                conn= self.connect_database()
                c= conn.cursor()
                x= c.execute("SELECT * FROM page")
                self.database_list= x.fetchall()
            except:
                print("Error")


            x={
            'id': str(int(self.database_list[-1][0])+1) if len(self.database_list) else "1",
            'stmp': stmp,
            'sno': str(len(self.rv.data)+1),
            'prd_name': prd_name,
            'tot_price': "₹"+str(int(price)),
            'paid_price': "₹"+str(int(paid)),
            'due_amnt':"₹"+str(int(price)- int(paid)) if int(price)-int(paid) else "NA",
            }
            self.rv.data.append(x)
            data= (prd_name,int(price), int(paid), int(price)- int(paid), int(stmp))
            conn= self.connect_database()

            if conn is not None:
                self.create_table(conn)
                self.insert_into_database(conn, data)

    #update any part of any data in listitems
    def update(self, new_val):

        conn= self.connect_database()

        #get corresponding id which will be used in updating database
        #from the self.list_index
        real_id= int(self.rv.data[self.list_index]['id'])
        
        if self.item_key=='tot_price' or self.item_key=='paid_price':
            #update the edited price
            try:
                temp= int(new_val)
                self.rv.data[self.list_index][self.item_key]= "₹"+new_val
                self.update_database(conn, real_id, self.item_key, new_val)

                #update the corresponding due_amnt
                due= int(self.rv.data[self.list_index]['tot_price'][1:])- int(self.rv.data[self.list_index]['paid_price'][1:])
                self.rv.data[self.list_index]['due_amnt']= "₹"+str(due) if due else "NA"
                self.update_database(conn, real_id, 'due_amnt', due)
            except:
                print("Error")

        elif len(new_val):
            self.rv.data[self.list_index][self.item_key]= new_val
            self.update_database(conn, real_id, self.item_key, new_val)

        self.rv.refresh_from_data()


    #delete a selected row from the view as well as from the database
    def delete(self):

        conn = self.connect_database()

        #get corresponding id which will be used in updating database
        #from the self.list_index
        real_id= int(self.rv.data[self.list_index]['id'])

        #remove element from the view list
        self.rv.data.remove(self.rv.data[self.list_index])

        #reset the view list
        try:
            for i in range(self.list_index, len(self.rv.data)):
                self.rv.data[i]["sno"]= str(int(self.rv.data[i]["sno"])-1)
        except IndexError as e:
            print(e)
        else:
            print("Error at 152")

        self.rv.refresh_from_data()

        #remove element from the database
        self.delete_from_database(conn, real_id)

    #connect to database
    def connect_database(self):
        try:
            conn=  sqlite3.connect(self.db)
            return conn
        except Error as e:
            print("Error: {}".format(e))

        return None

    #create database
    def create_table(self,conn):
        table= """
                CREATE TABLE IF NOT EXISTS page(
                id INTEGER PRIMARY KEY,
                prd_name VARCHAR NOT NULL,
                tot_price INT NOT NULL,
                paid_price INT NOT NULL,
                due_amnt INT,
                stmp INT NOT NULL
                )
                """


        try:
            c= conn.cursor()
            c.execute(table)
            conn.commit()

        except Error as e:
            print("Error: {}".format(e))

    #insert data into database
    def insert_into_database(self, conn, data):
        try:
            c= conn.cursor()
            c.execute(
            """
            INSERT INTO page
            (prd_name, tot_price, paid_price, due_amnt, stmp) VALUES (?,?,?,?,?)
            """, data
            )
            conn.commit()

        except Error as e:
            print("Error: {}".format(e))

    #update data into database
    def update_database(self, conn, index, field, field_val):
        try:
            c= conn.cursor()
            c.execute(
            """
            UPDATE page
            SET
                {}= ?
            WHERE id= ?
            """.format(field),
            (field_val, index))

            conn.commit()
        except Error as e:
            print("Error: {}".format(e))

    #delete specific data from database
    def delete_from_database(self, conn, index):
        try:
            c= conn.cursor()
            c.execute(
            """
            DELETE FROM page WHERE id=?
            """,
            (index,)
            )
            conn.commit()

        except Error as e:
            print("Error: {}".format(e))

    def update_data(self, name, id, value, item_key):
        p= EditPop()
        p.title= "Update {}({})".format(name,id)
        p.ids.prev_val.text= value
        p.open()
        self.list_index= int(id)-1
        self.item_key= item_key
        #print(p.ids.new_val)

    def delete_data(self, id):
        p= DeletePop()
        p.title= "Delete Row {}".format(id)
        p.open()
        self.list_index= int(id)-1

    #functions to animate
    def anim_out(self, instance):
        anim= Animation(
                        pos_hint={'y':0.2},
                        t= 'in_out_elastic',
                        d= 0.4,
                        )

        anim.start(instance)

    def anim_in(self, instance):
        anim= Animation(
                        pos_hint={'y':-1},
                        t= 'in_out_elastic',
                        d= 0.4
                        )
        anim.start(instance)




class ScreenManager(ScreenManager):
    pass

#MainApp
class Diary(App):

    def on_start(self):
        Clock.schedule_interval(self.update,0)
        self.root.ids.presScreen.ids.search_text.bind(
            text= self.root.ids.presScreen.ids.some_btn.setter('text'))

        #populate list if table exists in the database
        presScr= self.root.ids.presScreen
        conn= presScr.connect_database()
        c= conn.cursor()
        try:
            database_list= c.execute("SELECT * FROM page").fetchall()
            for i in range(len(database_list)):
                x={
                'id': str(database_list[i][0]),
                'stmp': database_list[i][5],
                'sno': str(i+1),
                'prd_name': str(database_list[i][1]),
                'tot_price': "₹"+str(database_list[i][2]),
                'paid_price': "₹"+str(database_list[i][3]),
                'due_amnt': "₹"+str(database_list[i][4]) if database_list[i][4] else "NA",
                }

                presScr.rv.data.append(x)
        except Error as e:
            print(e)


    def update(self, nap):
        self.root.ids.presScreen.ids.date.text= strftime("%a, %b. %d")
        self.root.ids.presScreen.ids.time.text= strftime("%I:%M:%S %p")

    def build(self):
        return Builder.load_file("gui.kv")


if __name__ == '__main__':
    Window.maximize()
    Diary().run()
