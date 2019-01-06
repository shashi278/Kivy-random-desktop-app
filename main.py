
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
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

import re
import glob
import os

#timestamp
tm= time.localtime()

#for databases
tmStmp=  "{}{}{}".format(tm.tm_mday,tm.tm_mon,tm.tm_year)

#search text
search_text=''


#class for the no search result screen
#class NoResultLayout(AnchorLayout):
#    pass

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
    rv= ObjectProperty()

    def populate_screen(self):
        self.rv.data=[]

        #list all databases files( .db files) except today's database
        all_files= [x for x in glob.glob("database\db_*.db") if re.findall('\d+', x)[0] != tmStmp]
        #print(all_files)

        for each in all_files:
            try:
                conn= self.connect_database(each)
                c= conn.cursor()
                datalist= c.execute("SELECT * FROM page").fetchall()
                temp_list= self.populate_view(datalist)
                #print(temp_list)
                self.rv.data.extend(temp_list)
            except Error as e:
                print("eRROR: {}".format(e))

    def populate_view(self, datalist):
        temp_list=[]
        #print('datalist: {}'.format(datalist))

        try:

            for i in range(len(datalist)):
                x={
                'id': str(datalist[i][0]),
                'stmp': datalist[i][5],
                'sno': str(i+1),
                'prd_name': str(datalist[i][1]),
                'tot_price': "₹"+str(datalist[i][2]),
                'paid_price': "₹"+str(datalist[i][3]),
                'due_amnt': "₹"+str(datalist[i][4]) if datalist[i][4] else "NA",
                }
                #print(x)

                temp_list.append(x)
            return temp_list
        except:
            print("Error may be in here")



    def connect_database(self, db):
        try:
            conn=  sqlite3.connect(db)
            return conn
        except Error as e:
            print("Error: {}".format(e))

        return None

#PresentScreen for current activities addition and changes
class PresentScreen(Screen):
    prod_name= ObjectProperty()
    tot_price= ObjectProperty()
    paid_price= ObjectProperty()
    #NoResLay= NoResultLayout()

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

            conn= self.connect_database()
            if conn is not None:
                try:
                    
                    c= conn.cursor()
                    x= c.execute("SELECT * FROM page")
                    self.database_list= x.fetchall()
                except Error as e:
                    print(e)


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
            print("Error:::: lol")

        self.rv.refresh_from_data()

        #remove element from the database
        self.delete_from_database(conn, real_id)

    #search for a given search_text
    def search(self):
        conn= self.connect_database()
        #list to store all the returned results
        returned_list=[]

        #if it's a numeric property then 'prop' would be 'tot_price'/'paid_price'/'due_amnt'
        #else it'd be 'prd_name'
        prop=[]
        try:
            dummy= int(search_text)
            prop= ["tot_price", "paid_price", "due_amnt"]

        except:
            prop= ["prd_name"]

        #print("prop: {}".format(prop))
        print("search_text: {}".format(search_text))

        for each in prop:
            temp_list= self.search_from_database(conn, each, search_text)
            if temp_list:
                #print("temp_list: ".format(temp_list))
                returned_list.extend(temp_list)

        returned_list= list(set(returned_list))
        print("returned list: {}".format(returned_list))
        #print("Everything's alright!")
        self.rv.data=[]

        if (len(search_text) and not returned_list):
            pass
            #print("Inside if part")
            #print("No result layout: {}".format(NoResultLayout()))
            #if not self.ids.list_area.ids.no_res_lay:
            #self.ids.list_area.ids.no_res_lay.size_hint=(1,1)
            #print("dummy in if: {}".format(self.ids.list_area.ids))
            
        elif (not len(search_text) and not returned_list):
            print("Inside elif part")
            try:
                #print("Is everything okay?")
                #if self.ids.list_area.ids.no_res_lay:
                #self.ids.list_area.ids.no_res_lay.size_hint=(0,0)
                c= conn.cursor()
                database_list= c.execute("SELECT * FROM page").fetchall()
                temp_list= self.populate_view(database_list)
                self.rv.data.extend(temp_list)
                #print("Database list: {}".format(database_list))
                #print("I think, I passed the test!")
            except:
                print("Some problem")

        else:
            print("Inside Else part")
            try:
                #try:
                #dummy= self.ids.list_area.ids
                #print("dummy: {}".format(dummy))
                #self.list_area.no_res_lay.size_hint=(0,0)
                #except:
                 #   print("error within try->try")

                temp_list= self.populate_view(returned_list)
                self.rv.data.extend(temp_list)
                #print("In the else try part")
            except:
                print("Some problem in else")

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

        if conn is not None:
            try:
                c= conn.cursor()
                c.execute(table)
                conn.commit()

            except Error as e:
                print("Error: {}".format(e))

    #insert data into database
    def insert_into_database(self, conn, data):
        if conn is not None:
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
        if conn is not None:
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
        if conn is not None:
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

    #search within the database
    def search_from_database(self, conn, prop, value):
        if conn is not None:
            try:
                c=conn.cursor()
                filtered_list= c.execute(
                    """
                    SELECT *
                    FROM page
                    WHERE {} LIKE ?
                    ORDER BY id;
                    """.format(prop),
                    (value+'%',)
                    ).fetchall()
                return filtered_list

            except Error as e:
                print(e)

        return None

    #populate view using data from a list
    def populate_view(self, datalist):

        temp_list=[]

        try:

            for i in range(len(datalist)):
                x={
                'id': str(datalist[i][0]),
                'stmp': datalist[i][5],
                'sno': str(i+1),
                'prd_name': str(datalist[i][1]),
                'tot_price': "₹"+str(datalist[i][2]),
                'paid_price': "₹"+str(datalist[i][3]),
                'due_amnt': "₹"+str(datalist[i][4]) if datalist[i][4] else "NA",
                }

                temp_list.append(x)
            return temp_list
        except:
            print("Error may be in here")


    #update function for update popup
    def update_data(self, name, id, value, item_key):
        p= EditPop()
        p.title= "Update {}({})".format(name,id)
        p.ids.prev_val.text= value
        p.open()
        self.list_index= int(id)-1
        self.item_key= item_key


    #delete function for the delete popup
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
            text=self.on_text)

        if not os.path.exists("database/"):
            os.makedirs("database/")

        #populate the presentScreen listview if 
        presScr= self.root.ids.presScreen

        conn= presScr.connect_database()
        if conn is not None:

            try:
                c= conn.cursor()
                database_list= c.execute("SELECT * FROM page").fetchall()
                temp_list= presScr.populate_view(database_list)
                presScr.rv.data.extend(temp_list)
            except Error as e:
                print(e)


    def update(self, nap):
        self.root.ids.presScreen.ids.date.text= strftime("%a, %b. %d")
        self.root.ids.presScreen.ids.time.text= strftime("%I:%M:%S %p")

    def build(self):
        return Builder.load_file("gui.kv")

    def on_text(self, instance, value):
        global search_text
        search_text= value
        self.root.ids.presScreen.search()

if __name__ == '__main__':
    Window.maximize()
    Diary().run()
