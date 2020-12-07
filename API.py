import json
import psycopg2
from sys import argv

def initialize(database, login, password):
    try:
        con = psycopg2.connect(dbname=database, user=login, host='localhost', password=password)
        cursor = con.cursor()
        cursor.execute(
            '''
            CREATE EXTENSION pgcrypto;
            '''
        )
        con.commit()
        cursor.execute(
            '''
            CREATE TABLE people (
            id integer,
            passwd varchar,
            data varchar
            );
            ''')
        cursor.execute(
            '''
            CREATE TABLE parents (
            id integer,
            parent integer
            );
            ''')
        cursor.execute(
            '''
            CREATE TABLE children (
            id integer,
            child integer
            );
            ''')
        con.commit()
        cursor.execute(
            '''
            CREATE USER app WITH LOGIN PASSWORD 'qwerty';
            '''
        )
        con.commit()
        cursor.execute(
            '''
            GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "people" TO app;
            '''
        )
        con.commit()
        cursor.execute(
            '''
            GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "parents" TO app;
            '''
        )
        con.commit()
        cursor.execute(
            '''
            GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "children" TO app;
            '''
        )
        con.commit()
        global init
        init = False
    except Exception:
        pass

def error(debug = ''):
    if debug == '':
        return json.dumps({"status": "ERROR"})
    else:
        return json.dumps({"status": "ERROR", "debug": debug})

def ok(data = ''):
    if data == '':
        return json.dumps({"status": "OK"})
    else:
        return json.dumps({"status": "OK", "data": data})

def connect(database, login, password):
    try:
        con = psycopg2.connect(dbname=database, user=login, host='localhost', password=password)
        cursor = con.cursor()
        return [ok(), cursor, con]
    except Exception as e:
        return [error(e), cursor, con]

def openf(args):
    database = args['database']
    login = args['login']
    password = args['password']
    if init:
        initialize(database, login, password)
    ret = connect(database, login, password)
    return ret

def check(id, cursor):
    cursor.execute(
        '''
        SELECT count(id) FROM people
        WHERE id = %d;
        '''
        % id
    )
    result = cursor.fetchall()
    if result[0][0] == 0:
        return True
    else:
        return False

def validate(id, passwd, cursor):
    cursor.execute(
        '''
        SELECT * FROM people
        WHERE id = %(id)d
        AND passwd = crypt('%(password)s', passwd);
        '''
        % {'id': id, 'password': passwd}
    )
    result = cursor.fetchall()
    if len(result) > 0:
        return True
    else:
        return False

def descendants_helper(args, children, cursor):
    descendants = children
    for i in children:
        args['emp'] = i
        i_children = json.loads(child(args, cursor))['data']
        if len(i_children) > 0:
            for j in i_children:
                descendants.append(j)
    return descendants
        
def descendants(args, cursor):
    temp_args = args
    try:
        children = json.loads(child(temp_args, cursor))['data']
        descendants = descendants_helper(temp_args, children, cursor)
        return ok(descendants)
    except Exception as e:
        return error(e)
                
def ancestors(args, cursor):
    temp_args = args
    loop = True
    ancestors = []
    try:
        while loop:
            emp_parent = json.loads(parent(temp_args, cursor))['data']
            if emp_parent != None:
                ancestors.append(emp_parent)
                temp_args['emp'] = emp_parent
            else:
                loop = False
        return ok(ancestors)
    except Exception as e:
        return error(e)

def child(args, cursor):
    emp = args['emp']
    children = []
    try:
        cursor.execute(
            '''
            SELECT child FROM children
            WHERE id = %d;
            '''
            % emp
        )
        result = cursor.fetchall()
        for i in result:
            children.append(i[0])
        return ok(children)
    except Exception as e:
        return error(e)

def parent(args, cursor):
    emp = args['emp']
    try:
        cursor.execute(
            '''
            SELECT parent FROM parents
            WHERE id = %d;
            '''
            % emp
        )
        result = cursor.fetchall()
        return ok(result[0][0])
    except Exception as e:
        return error(e)

def ancestor(args, cursor):
    emp1 = args['emp1']
    emp2 = args['emp2']
    temp_args = args
    temp_args['emp'] = emp1
    if json.loads(parent(temp_args, cursor))['data'] == emp2:
        return ok(True)
    if emp2 in json.loads(ancestors(temp_args, cursor))['data']:
        return ok(True)
    else:
        return ok(False)

def root(args, cursor, con):
    secret = args['secret']
    passwd = args['newpassword']
    data = args['data']
    emp = args['emp']
    if secret == 'qwerty':
        if check(emp, cursor):
            try:
                cursor.execute(
                    '''
                    INSERT INTO people(id, passwd, data) VALUES
                    (%(id)d, crypt('%(passwd)s', gen_salt('md5')), '%(data)s');
                    '''
                    % {'id': emp, 'passwd': passwd, 'data': data}
                )
                cursor.execute(
                    '''
                    INSERT INTO parents(id, parent) VALUES
                    (%(id)d, %(parent)s);
                    '''
                    % {'id': emp, 'parent': 'NULL'}
                )
                con.commit()
                return ok()
            except Exception as e:
                return error(e)
        else:
            return error("root already exists")
    else:
        return error("wrong secret")

def adder(parent, user, passwd, data, cursor, con):
    if check(user, cursor):
        cursor.execute(
            '''
            INSERT INTO people(id, passwd, data) VALUES
            (%(id)d, crypt('%(passwd)s', gen_salt('md5')), '%(data)s');
            '''
            % {'id': user, 'passwd': passwd, 'data': data}
        )
        cursor.execute(
            '''
            INSERT INTO parents(id, parent) VALUES
            (%(id)d, %(parent)d);
            '''
            % {'id': user, 'parent': parent}
        )
        cursor.execute(
            '''
            INSERT INTO children(id, child) VALUES
            (%(id)d, %(child)d);
            '''
            % {'id': parent, 'child': user}
        )
        con.commit()
        return ok()
    else:
        return error("person already in database")

def read_data(id, cursor):
    cursor.execute(
        '''
        SELECT data FROM people
        WHERE id = %d
        '''
        % id
    )
    data = cursor.fetchall()
    return ok(data[0][0])

def read(args, cursor):
    admin = args['admin']
    emp = args['emp']
    if emp == admin:
        return read_data(emp, cursor)
    if json.loads(parent(args, cursor)):
        return read_data(emp, cursor)
    if admin in json.loads(ancestors(args, cursor)):
        return read_data(emp, cursor)
    else:
        return error("can't read data")

def update_data(id, data, cursor, con):
    cursor.execute(
        '''
        UPDATE people SET data = '%(data)s'
        WHERE id = %(id)d
        '''
        % {'id': id, 'data': data}
    )
    con.commit()
    return ok()

def update(args, cursor, con):
    admin = args['admin']
    emp = args['emp']
    newdata = args['newdata']
    if emp == admin:
        return update_data(emp, newdata, cursor, con)
    if json.loads(parent(args, cursor)):
        return update_data(emp, newdata, cursor, con)
    if admin in json.loads(ancestors(args, cursor)):
        return update_data(emp, newdata, cursor, con)
    else:
        return error("can't update data")

def remove(args, cursor, con):
    emp = args['emp']
    delete = json.loads(descendants(args, cursor))['data']
    delete.append(emp)
    try:
        for i in delete:
            cursor.execute(
                '''
                DELETE FROM people
                WHERE id = %d;
                '''
                % i
            )
            cursor.execute(
                '''
                DELETE FROM parents
                WHERE id = %d;
                '''
                % i
            )
            cursor.execute(
                '''
                DELETE FROM children
                WHERE id = %(id)d
                OR child = %(id)d
                '''
                % {'id': i}
            )
            con.commit()
        return ok()
    except Exception as e:
        return error(e)

def new(args, cursor, con):
    admin = args['admin']
    data = args['data']
    newpasswd = args['newpasswd']
    emp1 = args['emp1']
    emp = args['emp']
    temp_args = args
    temp_args['emp'] = args['emp1']
    try:
        if admin == emp1:
            return adder(emp1, emp, newpasswd, data, cursor, con)
        elif admin in json.loads(ancestors(temp_args, cursor))['data']:
            return adder(emp1, emp, newpasswd, data, cursor, con)
        else:
            return error("wrong admin")
    except Exception as e:
        return error(e)

init = False
input_file = open(argv[1], 'r')
if len(argv) > 2:
    if argv[2] == '--init':
        init = True

while True:
    line = input_file.readline()
    if not line:
        break
    json_data = json.loads(line)
    task = list(json_data)[0]
    arguments = json_data[task]
    if task == 'open':
        status = openf(arguments)
        cursor = status[1]
        con = status[2]
        print(status[0])
    elif task == 'root':
        print(root(arguments, cursor, con))
    else:
        if validate(arguments['admin'], arguments['passwd'], cursor):
            if task == 'new':
                print(new(arguments, cursor, con))
            if task == 'remove':
                print(remove(arguments, cursor, con))
            if task == 'child':
                print(child(arguments, cursor))
            if task == 'parent':
                print(parent(arguments, cursor))
            if task == 'ancestors':
                print(ancestors(arguments, cursor))
            if task == 'descendants':
                print(descendants(arguments, cursor))
            if task == 'ancestor':
                print(ancestor(arguments, cursor))
            if task == 'read':
                print(read(arguments, cursor))
            if task == 'update':
                print(update(arguments, cursor, con))
        else:
            print(error("incorrect admin's password"))
