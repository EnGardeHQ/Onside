"""
GraphDB Service for Knowledge Graph

This service provides graph database functionality using Neo4j:
- Entity management (Companies, Competitors, Domains)
- Relationship mapping
- Graph queries and traversals
- Pattern matching
"""
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)


class GraphDBService:
    """Neo4j graph database service for knowledge graph operations."""

    def __init__(self, uri: str = "bolt://localhost:7687", username: str = "neo4j", password: str = "password"):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.driver.verify_connectivity()
            logger.info("GraphDB connection established successfully")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to GraphDB: {e}")
            raise

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("GraphDB connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def create_company(
        self,
        tenant_id: str,
        company_id: str,
        name: str,
        domain: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a company node in the graph.

        Args:
            tenant_id: Tenant identifier
            company_id: Company identifier
            name: Company name
            domain: Company domain
            properties: Additional properties

        Returns:
            Dict containing created company data
        """
        properties = properties or {}

        with self.driver.session() as session:
            result = session.execute_write(
                self._create_company_tx,
                tenant_id,
                company_id,
                name,
                domain,
                properties
            )
            logger.info(f"Created company node: {name}")
            return result

    @staticmethod
    def _create_company_tx(tx, tenant_id, company_id, name, domain, properties):
        query = """
        MERGE (c:Company {id: $company_id, tenant_id: $tenant_id})
        SET c.name = $name,
            c.domain = $domain,
            c.updated_at = datetime(),
            c += $properties
        RETURN c
        """
        result = tx.run(
            query,
            company_id=company_id,
            tenant_id=tenant_id,
            name=name,
            domain=domain,
            properties=properties
        )
        record = result.single()
        return dict(record["c"]) if record else {}

    def create_competitor(
        self,
        tenant_id: str,
        competitor_id: str,
        name: str,
        domain: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a competitor node in the graph.

        Args:
            tenant_id: Tenant identifier
            competitor_id: Competitor identifier
            name: Competitor name
            domain: Competitor domain
            properties: Additional properties

        Returns:
            Dict containing created competitor data
        """
        properties = properties or {}

        with self.driver.session() as session:
            result = session.execute_write(
                self._create_competitor_tx,
                tenant_id,
                competitor_id,
                name,
                domain,
                properties
            )
            logger.info(f"Created competitor node: {name}")
            return result

    @staticmethod
    def _create_competitor_tx(tx, tenant_id, competitor_id, name, domain, properties):
        query = """
        MERGE (comp:Competitor {id: $competitor_id, tenant_id: $tenant_id})
        SET comp.name = $name,
            comp.domain = $domain,
            comp.updated_at = datetime(),
            comp += $properties
        RETURN comp
        """
        result = tx.run(
            query,
            competitor_id=competitor_id,
            tenant_id=tenant_id,
            name=name,
            domain=domain,
            properties=properties
        )
        record = result.single()
        return dict(record["comp"]) if record else {}

    def create_relationship(
        self,
        from_id: str,
        to_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship between two entities.

        Args:
            from_id: Source entity ID
            to_id: Target entity ID
            relationship_type: Type of relationship (COMPETES_WITH, OWNS_DOMAIN, etc.)
            properties: Additional relationship properties

        Returns:
            Dict containing relationship data
        """
        properties = properties or {}

        with self.driver.session() as session:
            result = session.execute_write(
                self._create_relationship_tx,
                from_id,
                to_id,
                relationship_type,
                properties
            )
            logger.info(f"Created relationship: {from_id} -{relationship_type}-> {to_id}")
            return result

    @staticmethod
    def _create_relationship_tx(tx, from_id, to_id, rel_type, properties):
        query = f"""
        MATCH (from {{id: $from_id}})
        MATCH (to {{id: $to_id}})
        MERGE (from)-[r:{rel_type}]->(to)
        SET r.created_at = datetime(),
            r += $properties
        RETURN r, type(r) as rel_type
        """
        result = tx.run(query, from_id=from_id, to_id=to_id, properties=properties)
        record = result.single()
        if record:
            return {
                "type": record["rel_type"],
                "properties": dict(record["r"])
            }
        return {}

    def find_competitors(
        self,
        tenant_id: str,
        company_id: str,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Find competitors for a company.

        Args:
            tenant_id: Tenant identifier
            company_id: Company identifier
            depth: Relationship depth to traverse

        Returns:
            List of competitor dictionaries
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._find_competitors_tx,
                tenant_id,
                company_id,
                depth
            )
            logger.info(f"Found {len(result)} competitors for company {company_id}")
            return result

    @staticmethod
    def _find_competitors_tx(tx, tenant_id, company_id, depth):
        query = """
        MATCH (c:Company {id: $company_id, tenant_id: $tenant_id})
        MATCH (c)-[:COMPETES_WITH*1..%d]-(comp:Competitor)
        RETURN DISTINCT comp
        """ % depth

        result = tx.run(query, company_id=company_id, tenant_id=tenant_id)
        return [dict(record["comp"]) for record in result]

    def find_competitor_network(
        self,
        tenant_id: str,
        company_id: str
    ) -> Dict[str, Any]:
        """
        Find the complete competitor network for a company.

        Args:
            tenant_id: Tenant identifier
            company_id: Company identifier

        Returns:
            Dict containing network structure with nodes and relationships
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._find_network_tx,
                tenant_id,
                company_id
            )
            logger.info(f"Retrieved competitor network for company {company_id}")
            return result

    @staticmethod
    def _find_network_tx(tx, tenant_id, company_id):
        query = """
        MATCH (c:Company {id: $company_id, tenant_id: $tenant_id})
        MATCH path = (c)-[r:COMPETES_WITH*1..3]-(comp)
        WITH collect(path) as paths
        CALL apoc.convert.toTree(paths) yield value
        RETURN value
        """
        # Note: This requires APOC plugin. Alternative query without APOC:
        alt_query = """
        MATCH (c:Company {id: $company_id, tenant_id: $tenant_id})
        OPTIONAL MATCH (c)-[r]-(related)
        RETURN c as company, collect({node: related, relationship: type(r)}) as connections
        """

        result = tx.run(alt_query, company_id=company_id, tenant_id=tenant_id)
        record = result.single()

        if not record:
            return {"nodes": [], "relationships": []}

        return {
            "company": dict(record["company"]),
            "connections": [
                {
                    "node": dict(conn["node"]) if conn["node"] else None,
                    "relationship": conn["relationship"]
                }
                for conn in record["connections"]
            ]
        }

    def search_entities(
        self,
        tenant_id: str,
        entity_type: Optional[str] = None,
        search_term: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for entities in the graph.

        Args:
            tenant_id: Tenant identifier
            entity_type: Type of entity (Company, Competitor, Domain)
            search_term: Search term for name or domain
            limit: Maximum number of results

        Returns:
            List of matching entities
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._search_entities_tx,
                tenant_id,
                entity_type,
                search_term,
                limit
            )
            logger.info(f"Found {len(result)} entities matching search criteria")
            return result

    @staticmethod
    def _search_entities_tx(tx, tenant_id, entity_type, search_term, limit):
        label = f":{entity_type}" if entity_type else ""
        search_clause = ""

        if search_term:
            search_clause = "WHERE n.name CONTAINS $search_term OR n.domain CONTAINS $search_term"

        query = f"""
        MATCH (n{label} {{tenant_id: $tenant_id}})
        {search_clause}
        RETURN n
        LIMIT $limit
        """

        result = tx.run(
            query,
            tenant_id=tenant_id,
            search_term=search_term,
            limit=limit
        )
        return [dict(record["n"]) for record in result]

    def delete_entity(
        self,
        entity_id: str,
        tenant_id: str
    ) -> bool:
        """
        Delete an entity and its relationships.

        Args:
            entity_id: Entity identifier
            tenant_id: Tenant identifier

        Returns:
            True if deletion was successful
        """
        with self.driver.session() as session:
            result = session.execute_write(
                self._delete_entity_tx,
                entity_id,
                tenant_id
            )
            logger.info(f"Deleted entity: {entity_id}")
            return result

    @staticmethod
    def _delete_entity_tx(tx, entity_id, tenant_id):
        query = """
        MATCH (n {id: $entity_id, tenant_id: $tenant_id})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
        result = tx.run(query, entity_id=entity_id, tenant_id=tenant_id)
        record = result.single()
        return record["deleted_count"] > 0 if record else False

    def get_entity_by_id(
        self,
        entity_id: str,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get an entity by its ID.

        Args:
            entity_id: Entity identifier
            tenant_id: Tenant identifier

        Returns:
            Entity dictionary or None if not found
        """
        with self.driver.session() as session:
            result = session.execute_read(
                self._get_entity_tx,
                entity_id,
                tenant_id
            )
            return result

    @staticmethod
    def _get_entity_tx(tx, entity_id, tenant_id):
        query = """
        MATCH (n {id: $entity_id, tenant_id: $tenant_id})
        RETURN n, labels(n) as labels
        """
        result = tx.run(query, entity_id=entity_id, tenant_id=tenant_id)
        record = result.single()

        if not record:
            return None

        entity = dict(record["n"])
        entity["labels"] = record["labels"]
        return entity

    def run_cypher_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result dictionaries
        """
        parameters = parameters or {}

        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [dict(record) for record in result]


# Example usage and helper functions
def initialize_schema(graphdb: GraphDBService):
    """Initialize graph database schema with constraints and indexes."""
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (comp:Competitor) REQUIRE comp.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Domain) REQUIRE d.id IS UNIQUE",
    ]

    indexes = [
        "CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.tenant_id)",
        "CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name)",
        "CREATE INDEX IF NOT EXISTS FOR (comp:Competitor) ON (comp.tenant_id)",
        "CREATE INDEX IF NOT EXISTS FOR (comp:Competitor) ON (comp.domain)",
    ]

    for constraint in constraints:
        try:
            graphdb.run_cypher_query(constraint)
            logger.info(f"Created constraint: {constraint}")
        except Exception as e:
            logger.warning(f"Constraint creation failed (may already exist): {e}")

    for index in indexes:
        try:
            graphdb.run_cypher_query(index)
            logger.info(f"Created index: {index}")
        except Exception as e:
            logger.warning(f"Index creation failed (may already exist): {e}")
