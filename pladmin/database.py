import cx_Oracle, os, re, glob
from pladmin.files import Files as files

files = files()

class Database():

    db_admin_user          = os.getenv("DB_ADMIN_USER").upper()
    db_admin_password      = os.getenv("DB_ADMIN_PASSWORD")
    db_default_table_space = os.getenv("DB_DEFAULT_TABLE_SPACE").upper()
    db_temp_table_space    = os.getenv("DB_TEMP_TABLE_SPACE").upper()
    db_main_schema         = os.getenv("DB_MAIN_SCHEMA").upper()
    service_name           = os.getenv("DB_SERVICE_NAME")
    user                   = os.getenv("DB_USER").upper()
    password               = os.getenv("DB_PASSWORD")
    host                   = os.getenv("DB_HOST")
    port                   = os.getenv("DB_PORT")


    def __init__(self, displayInfo = False):
        self.types      = files.objectsTypes().keys()
        self.extentions = files.objectsTypes().values()
        
        self.displayInfo = displayInfo
        files.displayInfo = displayInfo


    def updateSchema(self):
        result = {}
        changes = files.localChanges()
        data = [files.pl_path + '/' + x for x in changes]

        invalids = self.createReplaceObject(path=data)
        
        # If some objects are invalids, try to compile again
        # if len(invalids):
            # self.compileObj(invalids)

        return invalids


    def createSchema(self):
        # To create users, give permission, etc. We need to connect with admin user using param asAdmin
        db = self.dbConnect(sysDBA=True)

        # Drop and create the user
        self.reCreateUser(db=db)
        exit()
        # Give grants to the user
        self.createGramtsTo(originSchema=self.db_main_schema, detinationSchema=self.user, db=db)

        # Create synonyms
        self.createSynonyms(originSchema=self.db_main_schema, detinationSchema=self.user, db=db)

        # Create o replace packages, views, functions and procedures (All elements in files.objectsTypes())
        data = files.listAllObjsFiles()
        self.createReplaceObject(path=data)
        
        # If some objects are invalids, try to compile
        invalids = self.getObjects(status='INVALID')
        self.compileObj(invalids)
        
        return invalids


    def getDBObjects(self):
        ''' << TODO >> '''
        db      = self.dbConnect(sysDBA=True)
        cursor  = db.cursor()

        # We need to get all object
        objects = self.getObjects()
        exit()

        # Get views 
        vSql = "SELECT view_name FROM dba_views WHERE owner = '%s'" % self.user
        bdViews = self.getData(query=vSql, db=db)

        oSql = "SELECT name, type, line, text FROM dba_source WHERE owner = '%s' and type IN ('%s')" % (self.user, types)
        dbObj = self.getData(query=oSql, db=db)

        # cursor.execute(sql)

 
    def compileObj(self, objList, db=None):

        localClose = False
        data = []

        if not db:
            db = self.dbConnect()
            localClose = True
        
        cursor = db.cursor()
        
        for obj in objList:
            sql = 'ALTER %s %s.%s COMPILE'%(obj['object_type'], obj['owner'], obj['object_name'])
            cursor.execute(sql)
            # data.extend(self.getObjErrors(owner=self.user, objName=fname, db=db))

        if localClose:
            db.close()

        return data


    def createReplaceObject(self, path=None, db=None):
        ''' 
        Create or Replace packges, views, procedures and functions 

        params: 
        ------
        path (array): path routes of the object on the file system
        db (cx_Oracle.Connection): If you opened a db connection puth here please to avoid

        return (list) with errors if some package were an error
        '''

        data = []
        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True
        
        cursor = db.cursor()

        progressTotal = len(path)
        files.progress(1, progressTotal, status='LISTING PACKAGES...', title='CREATE OR REPLACE PACKAGES')
        i = 2
        for f in path:

            fi = files.getFileName(f)
            fname = fi['name']
            ftype = fi['ext']

            # Display progress bar
            files.progress(i, progressTotal, 'CREATE OR REPLACE %s' % fname)
            i += 1


            # Only valid extencions sould be processed
            if not '.' + ftype in  self.extentions:
                continue

            opf = open(f, 'r')
            content = opf.read()
            opf.close()
            
            context = 'CREATE OR REPLACE '
            if ftype == 'vew':
                context = 'CREATE OR REPLACE FORCE VIEW %s AS \n' % fname
            
            cursor.execute(context + content)
            # print('INFO: Replaced %s.%s' % (fname, ftype))

            # Check if the object has some errors
            data.extend(self.getObjErrors(owner=self.user, objName=fname, db=db))

        
        return data
            

        if localClose:
            db.close()

        return data
    

    def getObjErrors(self, owner, objName, db=None):
        ''' Get object errors on execution time '''

        query = "SELECT * FROM all_errors WHERE owner = '%s' and NAME = '%s'" % (owner, objName)
        result = self.getData(query=query, db=db)
        
        return result


    def getObjects(self, status=None, withPath=False):
        # [] Se debe agregar a este metodo el porqué el objeto está invalido
        '''
        List invalid Packages, Functions and Procedures and Views
        
        Params:
        ------
        status (string): Valid values [VALID, INVALID].
        db (cx_Oracle) is an instance of cx_Oracle lib.

        return (dic) with all objects listed
        '''

        types = "', '".join(self.types)
        query = """
        SELECT     
            owner
            ,object_id
            ,object_name
            ,object_type
            ,status
            ,last_ddl_time
            ,created 
        FROM dba_objects WHERE owner = '%s' AND object_type in ('%s')""" % (self.user, types)

        # If re.match(r'VALID|INVALID', status):
        if ('INVALID' == status) or 'VALID' == status:
            query += " AND status = '%s'" % status

        # Return a dic with the data
        result = self.getData(query)

        if len(result) and withPath: 
            i = 0
            for obj in result:
                p = files.findObjFileByType(objType=obj['object_type'], objectName=obj['object_name'])
                result[i].update({'path': p[0]})
                i += 1

        return result


    def createGramtsTo(self, originSchema, detinationSchema, db=None):
        

        cursor  = db.cursor()
        cursor.execute("GRANT CREATE PROCEDURE TO %s" % detinationSchema)
        cursor.execute("GRANT CREATE SEQUENCE TO %s" % detinationSchema)
        cursor.execute("GRANT CREATE TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT CREATE VIEW TO %s" % detinationSchema)
        cursor.execute("GRANT CREATE TRIGGER TO %s" % detinationSchema)
        cursor.execute("GRANT EXECUTE ANY PROCEDURE TO %s" % detinationSchema)
        cursor.execute("GRANT SELECT ANY DICTIONARY TO %s" % detinationSchema)
        cursor.execute("GRANT CREATE SESSION TO %s" % detinationSchema)
        cursor.execute("GRANT SELECT ANY DICTIONARY TO %s" % detinationSchema)
        cursor.execute("GRANT EXECUTE ANY PROCEDURE TO %s" % detinationSchema)
        cursor.execute("GRANT EXECUTE ANY TYPE TO %s" % detinationSchema)
        cursor.execute("GRANT ALTER ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT ALTER ANY SEQUENCE TO %s" % detinationSchema)
        cursor.execute("GRANT UPDATE ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT DEBUG ANY PROCEDURE TO %s" % detinationSchema)
        cursor.execute("GRANT DEBUG CONNECT ANY to %s" % detinationSchema)
        cursor.execute("GRANT DELETE ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT ALTER ANY INDEX TO %s" % detinationSchema)
        cursor.execute("GRANT INSERT ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT READ ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT SELECT ANY TABLE TO %s" % detinationSchema)
        cursor.execute("GRANT SELECT ANY SEQUENCE TO %s" % detinationSchema)

        cursor.execute("GRANT UPDATE ON SYS.SOURCE$ TO %s" % detinationSchema)
        cursor.execute("GRANT EXECUTE ON SYS.DBMS_LOCK TO %s" % detinationSchema)
        cursor.execute("CREATE SYNONYM %s.FERIADOS FOR OMEGA.FERIADOS" % detinationSchema)


    def createSynonyms(self, originSchema, detinationSchema, db):
        """ Create synonyms types ('SEQUENCE', 'TABLE', 'TYPE') from originSchema to destinationSchema """


        cursor = db.cursor()
        sql = ''' SELECT oo.object_name, oo.object_type, oo.status
                FROM sys.dba_objects oo
                WHERE     oo.owner = '%s'
                    AND oo.object_type IN ('SEQUENCE', 'TABLE', 'TYPE')
                    AND oo.object_name NOT LIKE 'SYS_PLSQL_%%'
                    AND oo.object_name NOT LIKE 'QTSF_CHAIN_%%'
                    AND oo.object_name <> 'METADATA_TABLE'
                    AND NOT EXISTS
                            (SELECT 1
                                FROM sys.dba_objects tob
                                WHERE     tob.owner = '%s'
                                    AND tob.object_name = oo.object_name)
                    AND status = 'VALID' ''' % (originSchema, detinationSchema)

        synonyms = self.getData(query=sql, db=db)

        # Params to process bar
        progressTotal = len(synonyms)
        files.progress(1, progressTotal, 'LISTING TABLES', title='CREATE SYNONYM')

        i = 2
        for synon in synonyms:
            sql = "CREATE SYNONYM %s.%s FOR %s.%s" % (detinationSchema, synon['object_name'], originSchema, synon['object_name'])
            cursor.execute(sql)

            status = 'CREATE SYNONYM ' + detinationSchema + '.' + synon['object_name']
            if self.displayInfo:
                files.progress(i, progressTotal, status)
                i += 1
            
        cursor.close()


    def getData(self, query, params=None, db=None):
        ''' 
        List invalid Packages, Functions and Procedures and Views
        
        Params:
        ------
        query (string): SQL query data.
        db (cx_Oracle) is an instance of cx_Oracle lib.
        '''

        localClose = False
        if not db:
            db = self.dbConnect()
            localClose = True
        
        cursor = db.cursor()
        if not params:
            result = cursor.execute(query)
        else:
            result = cursor.execute(query, data)

        # Overriding rowfactory method to get the data in a dictionary
        result.rowfactory = self.makeDictFactory(result)

        # Fetching data from DB
        data = result.fetchall()

        # Close DB connection
        cursor.close()

        # If the connection was open on this method, close localy.
        if localClose:
            db.close()

        return data


    def reCreateUser(self, db):
        
        progressTotal = 3
        files.progress(count = 1, total=progressTotal, status='VALIDATING...', title = 'CREATE NEW USER')

        cursor = db.cursor()
        # Firts, we need to validate if the user exist
        sql = "SELECT COUNT(1) AS v_count FROM dba_users WHERE username = :db_user"
        cursor.execute(sql, {'db_user': self.user})

        
        # If user exist, drop it
        if cursor.fetchone()[0] > 0:
            files.progress(count = 2, total=progressTotal, status='DROP USER %s' % self.user)
            cursor.execute("DROP USER %s CASCADE" % self.user)

        # Create the user
        files.progress(count=2, total=progressTotal, status='CREATING USER %s' % self.user)
        sql = "CREATE USER %s IDENTIFIED BY %s DEFAULT TABLESPACE %s TEMPORARY TABLESPACE %s QUOTA UNLIMITED ON %s" % (
            self.user,
            self.password,
            self.db_default_table_space,
            self.db_temp_table_space,
            self.db_default_table_space
        )
        cursor.execute(sql)

        files.progress(count = 3, total=progressTotal, status='USER %s CREATED' % self.user, end=True)


    def dbConnect(self, sysDBA=False):
        '''
        Encharge to connect to Oracle database

        Params:
        -------
        sysDBA (boolean): True of False
        '''

        self.dsn = cx_Oracle.makedsn(self.host, self.port, service_name=self.service_name)
        user     = self.user
        password = self.password

        mode = 0
        if sysDBA:
            mode     = cx_Oracle.SYSDBA 
            user     = self.db_admin_user
            password = self.db_admin_password

        return cx_Oracle.connect(user=user, password=password, dsn=self.dsn, mode=mode, encoding="UTF-8")


    def makeDictFactory(self, cursor):
        ''' cx_Oracle library doesn't bring a simple way to convert a query result into a dictionary. '''
        columnNames = [d[0].lower() for d in cursor.description]
        def createRow(*args):
            return dict(zip(columnNames, args))

        return createRow
