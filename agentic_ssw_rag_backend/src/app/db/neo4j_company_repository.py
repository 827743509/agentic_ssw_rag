
from functools import lru_cache


from neo4j import GraphDatabase

from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent


from app.core.config import get_settings

settings=get_settings()


class Neo4jCompanyRepository:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_url,
            auth=(
                settings.neo4j_username,
                settings.neo4j_password,
            ),
        )
        self.database = settings.neo4j_database

    def close(self):
        self.driver.close()

    def find_child_companies(self, company_name: str, max_depth: int = 3):
        cypher = """
        MATCH path = (parent:Company {name: $company_name})-[:CONTROLS*1..3]->(child:Company)
        RETURN 
            child.companyId AS companyId,
            child.name AS name,
            length(path) AS depth
        ORDER BY depth ASC
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, company_name=company_name)
            rows = [dict(record) for record in result]

        if not rows:
            return f"没有查询到{company_name}的下级公司"

        return rows



    def find_job_by_params(self, company_name:list[str],job_city:list[str],company_city:list[str],publish_time_start:str,publish_time_end:str):
        where_list = []
        cypher = """
        MATCH (c:Company)-[:PUBLISHES]->(j:Job)
        """
        if(company_name):
            where_list.append(f"c.name in $company_name")
        if(job_city):
            where_list.append(f"j.city in $job_city")
        if(company_city):
            where_list.append(f"c.city in $company_city")
        if(publish_time_start):
            where_list.append(f"j.publishTime >= datetime($publish_time_start)")
        if(publish_time_end):
            where_list.append(f"j.publishTime <= datetime($publish_time_end)")
        if where_list:
            cypher += "WHERE " + " AND ".join(where_list)
        else:
            return f"请选择至少一个筛选条件"
        cypher+="""  
            RETURN c.name AS company,
            j.title AS title,
            j.salaryMin AS salaryMin,
            j.salaryMax AS salaryMax,
            j.city AS city
        ORDER BY j.publishTime
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(cypher,company_name=company_name, job_city=job_city,company_city=company_city,publish_time_start=publish_time_start,publish_time_end=publish_time_end)
            rows = [dict(record) for record in result]

        if not rows:
            return f"没有查询到发布的岗位"

        return rows


repo = Neo4jCompanyRepository()


def query_child_companies(company_id: str):
    """
    根据公司名称查询该公司的下级公司，最多查询3层。
    """
    return repo.find_child_companies(company_id)



def find_job_by_params(company_name:list[str],job_city:list[str],company_city:list[str],publish_time_start:str,publish_time_end:str):
    """
    根据公司名称(非必填),职位发布地区,公司所在地,职位发布时间查询该公司发布的岗位信息。
    """
    return repo.find_job_by_params(company_name,job_city,company_city,publish_time_start,publish_time_end)


child_company_tool = FunctionTool.from_defaults(
    fn=query_child_companies,
    name="query_child_companies",
    description="根据公司名称查询公司下级公司，适合回答公司控股、上下级、子公司关系问题。",
)

company_jobs_tool = FunctionTool.from_defaults(
    fn=find_job_by_params,
    name="query_company_jobs",
    description="根据公司名称(非必填),职位发布地区,公司所在地,职位发布时间查询该公司发布的岗位信息。",
)



