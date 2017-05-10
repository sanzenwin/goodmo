_sql_add_index = """
DROP PROCEDURE  
IF EXISTS add_index;  
delimiter //  
CREATE PROCEDURE add_index ()  
BEGIN  
DECLARE str VARCHAR (250);    
SET @str = concat(  
    ' ALTER TABLE ',  
    '{table_name}',  
    ' ADD INDEX ',  
    '{index_name}({index_field_list})'    
);  

SELECT  
    count(*) INTO @cnt  
FROM  
    INFORMATION_SCHEMA.STATISTICS
WHERE  
    TABLE_SCHEMA = '%(db_name)s'  
AND TABLE_NAME = '{table_name}'
AND INDEX_NAME = '{index_name}';  
  
IF @cnt <= 0 THEN  
    PREPARE stmt FROM @str;  
  EXECUTE stmt;  
END IF;  
  
END;  
//  
delimiter ;  
  
CALL add_index ();
select 1;
"""


def sql_add_index(table_name, index_name, *index_field_list):
    return """
        ' ALTER TABLE ',  
    'tbl_Follow',  
    ' ADD INDEX ',  
    'sm_followedID(sm_followedID,sm_followingID)' """
    return _sql_add_index.format(table_name=table_name, index_name=index_name,
                                 index_field_list=",".join(index_field_list))
