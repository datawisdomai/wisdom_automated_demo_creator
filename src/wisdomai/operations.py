"""Raw GraphQL operation strings.

Kept as module-level constants so callers can also reach into them when they
need to compose a one-off query without writing a new Client method.
"""

EXCHANGE_ACCESS_TOKEN = """
query ExchangeAccessToken($accessToken: String!) {
  exchangeAccessToken(accessToken: $accessToken)
}
"""

CURRENT_USER = """
query CurrentUser {
  currentUser {
    id
    email
    userAttributes { key value source }
  }
}
"""

# NB: the live Query field is `users(input: ListUsersInput)`, NOT `listUsers`
# (the latter is in some docs but is not in the schema — introspection caught it).
LIST_USERS = """
query ListUsers($input: ListUsersInput) {
  users(input: $input) {
    id
    email
    name
    creationTimestamp
    lastActiveSessionTimestamp
    isScimManaged
    userAttributes { key value source }
  }
}
"""

CREATE_USERS = """
mutation CreateUsers($input: CreateUsersInput!) {
  createUsers(input: $input) {
    status { code message }
  }
}
"""

SET_USER_ATTRIBUTES = """
mutation SetUserAttributes($input: SetUserAttributesInput!) {
  setUserAttributes(input: $input) {
    status { code message }
  }
}
"""

# NB: the docs describe `impersonateUser` as a mutation. In the live schema it
# is a *Query* field — sending it as `mutation` fails validation. It takes the
# permanent access key directly as an argument (not a Bearer header) and returns
# a 1-hour JWT for the impersonated user, which is what you feed to the embed
# URL's `?token=` param. SERVER-SIDE ONLY: never ship the access key to a browser.
IMPERSONATE_USER = """
query ImpersonateUser(
  $accessToken: String!
  $userEmail: String!
  $attributes: [UserAttributeInput!]
) {
  impersonateUser(
    accessToken: $accessToken
    userEmail: $userEmail
    attributes: $attributes
  )
}
"""

_APP_FIELDS = """
    id
    name
    description
    dashboardId
    accessLevel
    thumbnailUrl
    createdAt
    updatedAt
    owner { email }
"""

# Two live shapes for `apps`, depending on how far the tenant's build has moved:
#   newer (staging): apps(..., offset: Int!, limit: Int!) -> AppsResponse { nodes }
#   older (proddemo): apps(workspaceId: ID!)              -> [App!]!
# `Client.list_apps` tries the paginated form and falls back to the flat one.
LIST_APPS_PAGED = f"""
query Apps($workspaceId: ID!, $offset: Int!, $limit: Int!) {{
  apps(workspaceId: $workspaceId, offset: $offset, limit: $limit) {{
    nodes {{{_APP_FIELDS}}}
  }}
}}
"""

LIST_APPS = f"""
query Apps($workspaceId: ID!) {{
  apps(workspaceId: $workspaceId) {{{_APP_FIELDS}}}
}}
"""

GET_APP = """
query App($appId: ID!) {
  app(appId: $appId) {
    id
    name
    description
    workspaceId
    dashboardId
    accessLevel
    thumbnailUrl
    createdAt
    updatedAt
    owner { email }
  }
}
"""

DASHBOARDS = """
query Dashboards($scope: DashboardScope!, $domainId: String, $ownerId: String) {
  dashboards(scope: $scope, domainId: $domainId, ownerId: $ownerId) {
    nodes {
      id
      name
      createdAt
      accessLevel
      domains { id name }
      owner { id email }
    }
  }
}
"""

DASHBOARD = """
query Dashboard($id: String!, $scope: DashboardScope!, $version: String) {
  dashboard(id: $id, scope: $scope, version: $version) {
    id
    name
    description
    accessLevel
    widgets {
      id
      title
      widgetType
      layout { top left width height }
    }
  }
}
"""

REFRESH_DASHBOARD = """
mutation RefreshDashboard($id: String!, $version: String) {
  refreshDashboard(id: $id, version: $version) {
    id
    widgets { id title dataRefreshedAt }
  }
}
"""

CREATE_CONVERSATION = """
mutation CreateConversation($domainId: String!, $hidden: Boolean!) {
  id: createConversation(domainId: $domainId, hidden: $hidden)
}
"""

SEND_USER_MESSAGE = """
mutation SendUserMessage(
  $conversationId: String!
  $domainId: String!
  $query: DeltaInput!
) {
  sendUserMessage(
    conversationId: $conversationId
    domainId: $domainId
    query: $query
  ) {
    code
    message
  }
}
"""

SUBSCRIBE_CONVERSATION = """
subscription SubscribeConversation($auth: SubscriptionAuthInput!, $conversationId: String!) {
  subscribeConversation(auth: $auth, conversationId: $conversationId) {
    assistantMessageSent {
      id
      sender
      createdAt
      body { ops }
    }
    assistantResponseDiff {
      sender
      inProgress
      bodyDiff { ops }
    }
    assistantResponseCancelled
  }
}
"""


# ---- workspaces ----

WORKSPACES = """
query Workspaces {
  workspaces { id name }
}
"""

# ---- admin: connections ----

# Connections are workspace-scoped. `connections` returns a ConnectionsResponse
# wrapper (`nodes`), and a Connection carries no top-level name — it lives in
# `details.name` (verified by introspection on proddemo, 2026-10-12). A 403 here
# means the API key's user is not a member of that workspace.
LIST_CONNECTIONS = """
query Connections($workspaceID: ID) {
  connections(workspaceID: $workspaceID) {
    nodes {
      id
      createdAt
      details {
        name
        description
        dialect
        dataSourceType
        connectionType
        snowflake { account warehouse user role databaseFilters }
        teradata { host port username databaseFilters }
      }
    }
  }
}
"""

# ---- admin: domains ----

# domainsLightweight requires BOTH workspaceID and limit (the server rejects
# the call otherwise). Get the workspace id from the WORKSPACES query — most
# tenants have a single "Default Organization" workspace.
LIST_DOMAINS = """
query DomainsLightweight($workspaceID: ID!, $limit: Int!, $offset: Int) {
  domainsLightweight(workspaceID: $workspaceID, limit: $limit, offset: $offset) {
    totalCount
    nodes { id name updatedAt isHidden }
  }
}
"""

CREATE_DOMAIN = """
mutation CreateDomain($input: CreateDomainInput!) {
  createDomain(input: $input) {
    id
    version
    name
    description
  }
}
"""

DUPLICATE_DOMAIN = """
mutation DuplicateDomain($id: ID!, $workspaceID: ID) {
  duplicateDomain(id: $id, workspaceID: $workspaceID) {
    id
    version
    name
    description
  }
}
"""

# Attach a connection's database (and its tables) to a domain. Replaces the old
# `dataSourcesUpdate` mutation, which was removed from the schema; the data-source
# surface is now database-grained (a connection + database name) rather than a
# per-table list. Returns the updated DomainModel.
ADD_DATABASE_TO_DOMAIN = """
mutation AddDatabaseToDomain($input: AddDatabaseToDomainInput!) {
  addDatabaseToDomain(input: $input) {
    id
    name
  }
}
"""

# ---- admin: connections ----

# Create a new connection. `details` is a ConnectionDetailsInput, whose shape is
# specific to the connection type (Snowflake, BigQuery, etc.) — introspect
# ConnectionDetailsInput for the exact fields. Corrects the old "connection
# creation is not exposed" note: connectionCreate IS in the live schema.
CONNECTION_CREATE = """
mutation ConnectionCreate($details: ConnectionDetailsInput!, $skipValidation: Boolean, $workspaceID: ID) {
  connectionCreate(details: $details, skipValidation: $skipValidation, workspaceID: $workspaceID) {
    id
    details { name connectionType }
  }
}
"""

GET_CONNECTION = """
query GetConnection($id: ID!) {
  connection(id: $id) {
    id
    details { name connectionType }
    status {
      lastRun { status startedAt endedAt conciseErrorMessage }
      lastSuccessfulRun { status startedAt endedAt }
    }
  }
}
"""

CONNECTION_REFRESH = """
mutation ConnectionRefresh($id: ID!) {
  connectionRefresh(id: $id)
}
"""

# ---- admin: knowledge (semantic context) ----

GET_DOMAIN_KNOWLEDGE = """
query GetDomainKnowledge($domainId: ID!) {
  domain(id: $domainId) {
    id
    knowledge { name description updatedAt updatedBy { id email } }
  }
}
"""

ADD_KNOWLEDGE = """
mutation AddKnowledge($domainId: ID!, $knowledgeEntries: [KnowledgeInput!]!) {
  addKnowledge(domainId: $domainId, knowledgeEntries: $knowledgeEntries) {
    id
    knowledge { name description }
  }
}
"""

UPDATE_KNOWLEDGE = """
mutation UpdateKnowledge(
  $domainId: ID!
  $oldKnowledge: KnowledgeInput!
  $updatedKnowledge: KnowledgeInput!
) {
  updateKnowledge(
    domainId: $domainId
    oldKnowledge: $oldKnowledge
    updatedKnowledge: $updatedKnowledge
  ) {
    id
    knowledge { name description }
  }
}
"""

DELETE_KNOWLEDGE = """
mutation DeleteKnowledge($domainId: ID!, $knowledge: KnowledgeInput!) {
  deleteKnowledge(domainId: $domainId, knowledge: $knowledge) {
    id
    knowledge { name description }
  }
}
"""


# ---- evaluation sets and runs ----
# These operations are present in the live GraphQL schema but are NOT in the
# public docs as of 2026-06. Surface confirmed via introspection.
# Items are nested twice: `items[session_index][turn_index]` — outer list is
# a multi-turn test session, inner list is each turn within that session.

_EVAL_SET_FIELDS = """
  id version name domainId evalSetType
  createdAt updatedAt cronExpression cronTimezone draftId
"""

_PROMPT_EVAL_FIELDS = """
  manualScore manualFeedback
  softEvalScore softEvalFeedback
  matchedGtSqlIndex
  gtError generatedError
"""

_EVAL_RUN_FIELDS = f"""
  id evalSetId evalSetVersion evalSetName evalSetType
  conversationIds createdAt completedAt cancelledAt
  selectedModelName experimentalMode runGroupId draftId draftName
  overallCombinedScore previousCompletedRunScore
  pageInfo {{
    totalSessions totalPromptCount totalCombinedEvalScore hasNextPage hasPreviousPage
  }}
  prompts
  evaluations {{
    {_PROMPT_EVAL_FIELDS}
  }}
"""

LIST_EVAL_SETS = f"""
query ListEvalSets($domainId: ID!, $draftId: ID) {{
  evalSets(domainId: $domainId, draftId: $draftId) {{
    {_EVAL_SET_FIELDS}
  }}
}}
"""

CREATE_EVAL_SET = f"""
mutation CreateEvalSet($input: CreateEvalSetInput!) {{
  createEvalSet(input: $input) {{
    {_EVAL_SET_FIELDS}
    items {{ prompt sql }}
  }}
}}
"""

UPDATE_EVAL_SET = f"""
mutation UpdateEvalSet($input: UpdateEvalSetInput!) {{
  updateEvalSet(input: $input) {{
    {_EVAL_SET_FIELDS}
    items {{ prompt sql }}
  }}
}}
"""

DELETE_EVAL_SET = """
mutation DeleteEvalSet($input: DeleteEvalSetInput!) {
  deleteEvalSet(input: $input)
}
"""

RUN_EVALUATION = """
mutation RunEvaluation(
  $domainId: String!
  $existingEvalSetId: String!
  $existingRunId: String
  $selectedModelName: String
  $parallelization: Int
  $runCount: Int
  $draftId: ID
  $experimentalMode: ExperimentalMode
) {
  runEvaluation(
    domainId: $domainId
    existingEvalSetId: $existingEvalSetId
    existingRunId: $existingRunId
    selectedModelName: $selectedModelName
    parallelization: $parallelization
    runCount: $runCount
    draftId: $draftId
    experimentalMode: $experimentalMode
  )
}
"""

CANCEL_EVALUATION_RUN = """
mutation CancelEvaluationRun($id: ID!) {
  cancelEvaluationRun(id: $id)
}
"""

GET_EVALUATION_RUN = f"""
query EvaluationRun($id: ID!, $page: Int, $pageSize: Int) {{
  evaluationRun(id: $id, page: $page, pageSize: $pageSize) {{
    {_EVAL_RUN_FIELDS}
  }}
}}
"""

LIST_EVALUATION_RUNS = """
query EvaluationRuns(
  $workspaceID: ID
  $filter: EvaluationRunsFilterInput!
  $offset: Int
  $limit: Int
) {
  evaluationRuns(
    workspaceID: $workspaceID
    filter: $filter
    offset: $offset
    limit: $limit
  ) {
    id evalSetId evalSetVersion evalSetName evalSetType
    conversationIds createdAt completedAt cancelledAt
    selectedModelName experimentalMode runGroupId draftId draftName
    promptCount overallCombinedScore previousCompletedRunScore
  }
}
"""

GET_EVALUATION_RUN_GROUP = f"""
query EvaluationRunGroup($runGroupId: ID!, $workspaceId: ID) {{
  evaluationRunGroup(runGroupId: $runGroupId, workspaceId: $workspaceId) {{
    runGroupId
    totalSamples consistentlyPassing consistentlyFailing flaky
    sampleConsistency {{
      itemId subItemId prompt passCount totalRuns status
    }}
    runs {{
      {_EVAL_RUN_FIELDS}
    }}
  }}
}}
"""

GET_EVAL_ANALYSIS_STATUS = """
query EvalAnalysisStatus($domainId: String!) {
  getEvalAnalysisStatus(domainId: $domainId) {
    analysisStatus lastAnalysisCompletedAt schemaHealthScore
    activeEvalRunId activeEvalRunGroupId
    latestRqEvalRunId latestRqEvalRunGroupId
    lastEvalStatus
    lastEvalExecutionStatus lastSchemaExecutionStatus lastUsageExecutionStatus
  }
}
"""

UPDATE_EVALUATION_RUN = """
mutation UpdateEvaluationRun($id: ID!, $input: UpdateEvaluationRunInput!) {
  updateEvaluationRun(id: $id, input: $input) {
    success evalSetUpdated gtSqlAdded gtSqlRemoved
  }
}
"""

CREATE_EVALSET_FROM_REVIEWED_QUERIES = """
mutation CreateEvalsetFromReviewedQueries(
  $domainId: String!
  $runEval: Boolean
  $tags: [String!]
  $runCount: Int
  $experimentalMode: ExperimentalMode
) {
  createEvalsetFromReviewedQueries(
    domainId: $domainId
    runEval: $runEval
    tags: $tags
    runCount: $runCount
    experimentalMode: $experimentalMode
  ) {
    evalsetId evalsetName itemCount runId runGroupId
  }
}
"""

SCHEDULE_EVAL_SET = f"""
mutation ScheduleEvalSet($evalSetId: ID!, $cronExpression: String, $cronTimezone: String) {{
  scheduleEvalSet(
    evalSetId: $evalSetId
    cronExpression: $cronExpression
    cronTimezone: $cronTimezone
  ) {{
    {_EVAL_SET_FIELDS}
  }}
}}
"""

PAUSE_SCHEDULED_EVAL = """
mutation PauseScheduledEval($domainId: String!, $evalSetId: String!) {
  pauseScheduledEval(domainId: $domainId, evalSetId: $evalSetId)
}
"""

# includeSchemaAnalysis was removed from the live schema on proddemo (verified 2026-10-16).
TRIGGER_EVAL_ANALYSIS = """
mutation TriggerEvalAnalysis(
  $domainId: String!
  $requireRqEval: Boolean
) {
  triggerEvalAnalysis(
    domainId: $domainId
    requireRqEval: $requireRqEval
  ) {
    status message evalRunId runGroupId
  }
}
"""

# ---- table inspection + SQL execution ----
# Also undocumented; confirmed via introspection 2026-06. On CSV-backed domains
# the warehouse database is `wisdom_storage` and the SQL dialect is `duckdb`.

GET_DOMAIN_TABLES = """
query GetDomainTables($id: ID!) {
  domain(id: $id) {
    id
    name
    databases {
      id
      name
      type
      tables {
        id
        name
        displayName
        isUserCSVTable
        columns { name dataType description }
      }
    }
  }
}
"""

TABLE_PREVIEW = """
query TablePreview($tableId: ID!, $domainId: ID!, $limit: Int, $offset: Int) {
  tablePreview(tableId: $tableId, domainId: $domainId, limit: $limit, offset: $offset) {
    totalRows
    hasMore
    columns { name }
    data { value }
  }
}
"""

RUN_SQL_QUERY = """
mutation RunSqlQuery(
  $domainId: String!
  $sql: String!
  $dialect: String
  $databaseName: String
) {
  runSqlQuery(
    domainId: $domainId
    sql: $sql
    dialect: $dialect
    databaseName: $databaseName
  ) {
    traceId
    visualization {
      totalRows
      columns { name }
      data { value }
    }
  }
}
"""

# ---- CSV upload (structured table ingest) ----
# IMPORTANT: this is the path the docs claim doesn't exist. `upload_document`
# (unstructured docs) is genuinely unimplemented, but a CSV becomes a real
# warehouse table via: generateSignedUrlsForCSVUpload -> HTTP PUT bytes ->
# processCsv. Column names get sanitized (spaces/symbols -> underscores).

GENERATE_CSV_UPLOAD_URLS = """
mutation GenerateCsvUploadUrls($filenames: [String!]!) {
  generateSignedUrlsForCSVUpload(filenames: $filenames) {
    signedUrl
    key
    bucketType
    bucketDescriptor
  }
}
"""

PROCESS_CSV = """
mutation ProcessCsv($data: ProcessCsvRequestInput!) {
  processCsv(data: $data) {
    domainId
    tableId
  }
}
"""

DELETE_CSV_TABLE = """
mutation DeleteCsvTable($id: ID!, $domainId: ID!, $rawFilePath: String!) {
  deleteUnstructuredCsvTable(id: $id, domainId: $domainId, rawFilePath: $rawFilePath)
}
"""

# ---- reviewed queries ----
# The reviewed-query lifecycle (question + SQL pairs that teach the domain).
# `addSqlReviewedQueryItems` items are {query, sql, dialect}. Also undocumented.

GET_REVIEWED_QUERY_ITEMS = """
query GetReviewedQueryItems($domainId: String!, $limit: Int, $offset: Int, $draftId: ID) {
  getReviewedQueryItems(domainId: $domainId, limit: $limit, offset: $offset, draftId: $draftId) {
    nodes {
      id
      question
      answerType
      isAnswerExecutable
      enabled
      createdAt
      updatedAt
      answerCodeObj { codeStr dialect }
    }
    pageInfo { totalCount }
  }
}
"""

ADD_SQL_REVIEWED_QUERY_ITEMS = """
mutation AddSqlReviewedQueryItems(
  $domainId: String!
  $reviewedQuerySqlQueries: [ReviewedQuerySqlItem!]!
  $draftId: ID
) {
  addSqlReviewedQueryItems(
    domainId: $domainId
    reviewedQuerySqlQueries: $reviewedQuerySqlQueries
    draftId: $draftId
  ) {
    id
    question
    isAnswerExecutable
  }
}
"""

DELETE_REVIEWED_QUERY_ITEMS = """
mutation DeleteReviewedQueryItems($ids: [ID!]!, $domainId: String!, $draftId: ID) {
  deleteReviewedQueryItems(ids: $ids, domainId: $domainId, draftId: $draftId)
}
"""

# ---- knowledge extraction + modeling suggestions (the "context extractor") ----
# Also undocumented; introspected 2026-06. `triggerKnowledgeExtraction` runs the
# extractor over an uploaded spec/file; it emits MMSuggestion items (knowledge,
# column/table descriptions, metrics, formulas, joins, reviewed queries) that you
# then apply. GOTCHA: the suggestion `task.type` is read back as
# `MM_SUGGESTION_TASK_TYPE_X` but the INPUT enum wants the bare `X`
# (e.g. `ADD_LEARNED_METRIC`, `ADD_MISSING_JOINS`). `createModelingSuggestion`
# returns only a Boolean — re-fetch to get the new id, then apply.

KNOWLEDGE_EXTRACTION_RUNS = """
query KnowledgeExtractionRuns($domainId: ID!, $limit: Int, $offset: Int) {
  knowledgeExtractionRuns(domainId: $domainId, limit: $limit, offset: $offset) {
    totalCount
    runs {
      sourceConnectionId
      jobRun { jobRunId jobType status startedAt endedAt summary conciseErrorMessage }
      files { runFileId status sourceType sourceMetadataJson }
    }
  }
}
"""

GET_MODELING_SUGGESTIONS = """
query GetModelingSuggestions($domainId: ID!, $includeAllStatuses: Boolean, $jobRunId: String, $draftId: ID) {
  modelingSuggestion(domainId: $domainId, includeAllStatuses: $includeAllStatuses, jobRunId: $jobRunId, draftId: $draftId) {
    nodes {
      id
      status
      source
      priority
      task {
        type
        addLearnedKnowledge { name knowledgeStr }
        addLearnedMetric { metricName metricExpression metricDescription }
        addLearnedFormula { sourceName formulaName formulaExpression }
        enterTableDescription { sourceName description }
        addColumnDescription { columnName description }
        addReviewedQuery { question code }
        addMissingJoin { leftSourceId rightSourceId relationshipType }
        textSuggestion { suggestion explanation }
        upsertSkill { skillId name newMarkdown baseVersion }
      }
    }
  }
}
"""

APPLY_MODELING_SUGGESTIONS = """
mutation ApplyModelingSuggestions($domainId: ID!, $suggestionIds: [ID!]!, $draftId: ID) {
  applyModelingSuggestions(domainId: $domainId, suggestionIds: $suggestionIds, draftId: $draftId) {
    suggestionId
    success
    errorMessage
  }
}
"""

UNDO_MODELING_SUGGESTIONS = """
mutation UndoModelingSuggestions($domainId: ID!, $suggestionIds: [ID!]!) {
  undoModelingSuggestions(domainId: $domainId, suggestionIds: $suggestionIds) {
    suggestionId
    success
    errorMessage
  }
}
"""

CREATE_MODELING_SUGGESTION = """
mutation CreateModelingSuggestion(
  $domainId: ID!
  $task: MMSuggestionTaskInput!
  $source: MMSuggestionSource!
) {
  createModelingSuggestion(domainId: $domainId, task: $task, source: $source)
}
"""

PATCH_MODELING_SUGGESTION = """
mutation PatchModelingSuggestion($data: MMSuggestionInput!) {
  patchModelingSuggestion(data: $data)
}
"""


# ---- demo creator additions (verified by introspection on proddemo, 2026-10-12) ----

# Metrics: a SQL metric is an aggregate expression over TABLE.COLUMN references,
# e.g. "SUM(CUSTOMERS.ANNUAL_CONTRACT_VALUE)" — exactly what the metrics.csv
# "SQL" column holds. validateMetric is a *query*; run it before createMetric.
VALIDATE_METRIC = """
query ValidateMetric($domainId: ID!, $data: MetricInput!) {
  validateMetric(domainId: $domainId, data: $data) {
    definitionType
    expandedExpression
    directTables { name databaseName schemaName }
  }
}
"""

CREATE_METRIC = """
mutation CreateMetric($domainId: ID!, $data: MetricInput!) {
  createMetric(domainId: $domainId, data: $data) {
    id name displayName definitionType authoredExpression
  }
}
"""

UPDATE_METRIC = """
mutation UpdateMetric($domainId: ID!, $metricId: ID!, $data: MetricInput!) {
  updateMetric(domainId: $domainId, metricId: $metricId, data: $data) { id name authoredExpression }
}
"""

DELETE_METRIC = """
mutation DeleteMetric($domainId: ID!, $metricId: ID!) {
  deleteMetric(domainId: $domainId, metricId: $metricId)
}
"""

GET_DOMAIN_METRICS = """
query DomainMetrics($id: ID!) {
  domain(id: $id) {
    id
    domainSystemInstructions
    metrics { id name displayName description definitionType authoredExpression displayFormat precision visibility
              directTables { name databaseName schemaName } }
  }
}
"""

# Tables with ids/versions and the per-column settings we manage (NER lookup, visibility).
GET_DOMAIN_TABLE_COLUMNS = """
query DomainTableColumns($id: ID!) {
  domain(id: $id) {
    id
    databases {
      name
      tables { id version name columns { name nerMode visibility isPrimaryKey description } }
    }
  }
}
"""

UPDATE_TABLE_COLUMNS = """
mutation UpdateTableColumns($domainId: ID!, $tableId: ID!, $tableVersion: Int!, $data: ColumnBulkInput!) {
  updateTableColumns(domainId: $domainId, tableId: $tableId, tableVersion: $tableVersion, data: $data) { id version }
}
"""

UPDATE_DOMAIN_CONFIG = """
mutation UpdateDomainConfig($domainId: ID!, $data: DomainConfigInput!) {
  updateDomainConfig(domainId: $domainId, data: $data) { id version name domainSystemInstructions }
}
"""

# Unstructured documents for the Context Extractor: signed URL -> HTTP PUT ->
# register -> trigger extraction. Read back with contextExtractionUploadedFiles.
GENERATE_SIGNED_URLS_FOR_KNOWLEDGE_EXTRACTION = """
mutation SignedUrlsForKnowledgeExtraction($domainId: ID!, $filenames: [String!]!) {
  generateSignedUrlsForKnowledgeExtraction(domainId: $domainId, filenames: $filenames) {
    signedUrl key bucketType bucketDescriptor
  }
}
"""

REGISTER_CONTEXT_EXTRACTION_UPLOADED_FILES = """
mutation RegisterContextExtractionUploadedFiles($input: RegisterContextExtractionUploadedFilesInput!) {
  registerContextExtractionUploadedFiles(input: $input) { __typename }
}
"""

ATTACH_CONTEXT_EXTRACTION_CONNECTION = """
mutation AttachContextExtractionConnection($domainId: ID!, $connectionId: ID!, $acceptanceStrategy: AcceptanceStrategy, $autoExtractEnabled: Boolean) {
  attachContextExtractionConnection(domainId: $domainId, connectionId: $connectionId, acceptanceStrategy: $acceptanceStrategy, autoExtractEnabled: $autoExtractEnabled) { __typename }
}
"""

TRIGGER_KNOWLEDGE_EXTRACTION = """
mutation TriggerKnowledgeExtraction($input: TriggerKnowledgeExtractionInput!) {
  triggerKnowledgeExtraction(input: $input) { __typename }
}
"""

CONTEXT_EXTRACTION_UPLOADED_FILES = """
query ContextExtractionUploadedFiles($input: GetContextExtractionUploadedFilesInput!) {
  contextExtractionUploadedFiles(input: $input) { sourceFileId fileName instructions acceptanceStrategy }
}
"""

DOMAIN_CONTEXT_EXTRACTION_CONNECTIONS = """
query DomainContextExtractionConnections($id: ID!) {
  domain(id: $id) { id contextExtractionConnectionIds datasetConnectionIds datasets { id name ownerConnectionId } }
}
"""

# Unstructured documents as domain DATA (files the AI reasons over): dataset files.
GENERATE_DATASET_ID_FOR_DOMAIN = """
mutation GenerateDatasetIdForDomain($domainId: ID!) { generateDatasetIdForDomain(domainId: $domainId) }
"""

GENERATE_SIGNED_URLS_FOR_DATASET_FILES = """
mutation SignedUrlsForDatasetFiles($datasetId: ID!, $domainId: ID, $filenames: [String!]!) {
  generateSignedUrlsForDatasetFiles(datasetId: $datasetId, domainId: $domainId, filenames: $filenames) {
    signedUrl key bucketType bucketDescriptor
  }
}
"""

HANDLE_DATASET_FILE_UPLOAD = """
mutation HandleDatasetFileUpload($datasetId: String!, $domainId: String, $rawFilePaths: [String!]!) {
  handleDatasetFileUpload(datasetId: $datasetId, domainId: $domainId, rawFilePaths: $rawFilePaths)
}
"""

FILES_FOR_DATASET = """
query FilesForDataset($datasetId: ID!, $domainId: ID!) {
  filesForDataset(datasetId: $datasetId, domainId: $domainId) { __typename }
}
"""

# Live Apps
CREATE_APP = """
mutation CreateApp($workspaceId: ID!, $name: String!, $domainId: ID!) {
  createApp(workspaceId: $workspaceId, name: $name, domainId: $domainId) {
    id name description workspaceId dashboardId domainId liveSpecVersion hasUnpublishedChanges
  }
}
"""

GET_APP_FULL = """
query AppFull($appId: ID!) {
  app(appId: $appId) {
    id name description workspaceId dashboardId domainId liveSpecVersion hasUnpublishedChanges dashboardVersion updatedAt
  }
}
"""

PUBLISH_APP_DRAFT = """
mutation PublishAppDraft($appId: ID!, $note: String) {
  publishAppDraft(appId: $appId, note: $note) { id liveSpecVersion hasUnpublishedChanges }
}
"""

ACTIVE_APP_CONVERSATION = """
query ActiveAppConversation($appId: ID!) { activeAppConversation(appId: $appId) { __typename } }
"""

SET_ACTIVE_APP_CONVERSATION = """
mutation SetActiveAppConversation($appId: ID!, $conversationId: ID) {
  setActiveAppConversation(appId: $appId, conversationId: $conversationId) { __typename }
}
"""

CREATE_CONVERSATION_FULL = """
mutation CreateConversationFull($domainId: String, $hidden: Boolean!, $workspaceId: String, $liveAppEditPolicy: LiveAppEditPolicy, $requestChannelType: RequestChannelType, $channelSourceId: String) {
  id: createConversation(domainId: $domainId, hidden: $hidden, workspaceId: $workspaceId, liveAppEditPolicy: $liveAppEditPolicy, requestChannelType: $requestChannelType, channelSourceId: $channelSourceId)
}
"""

# Agents (workflow agents built from a prompt)
# 2026-10-26: the result lost `workflowJson agentName` and now returns a full
# `specification: AnalysisScheduleTask` (the shape createWorkflowAgent takes as input).
GENERATE_WORKFLOW_FROM_PROMPT = """
mutation GenerateWorkflowFromPrompt($input: GenerateWorkflowFromPromptInput!) {
  generateWorkflowFromPrompt(input: $input) {
    message
    specification {
      agentName analysisDomainId analysisDescription useDeepAnalysis instruction triggerCriteria
      workflow {
        nodes {
          id type title positionX positionY handle
          instruction { ops { insert { text } } }
          config {
            domainId triggerType
            timing { intervalInMins startTime cronExpression cronTimezone }
            delivery { type emailConfig { toEmailIds } slackConfig { channelNames } teamsConfig { userEmails } webhookConfig { webhookUrls } }
            routeMap { condition { ops { insert { text } } } edgeId branchIndex }
          }
        }
        edges { id fromNodeId toNodeId }
        canvasAnnotation { notes { id text positionX positionY } }
      }
    }
  }
}
"""

CREATE_WORKFLOW_AGENT = """
mutation CreateWorkflowAgent($specification: AnalysisScheduleTaskInput!, $workspaceID: ID, $asDraft: Boolean) {
  createWorkflowAgent(specification: $specification, workspaceID: $workspaceID, asDraft: $asDraft) {
    id isDraft version scheduleId specification { agentName analysisDomainId analysisDescription }
  }
}
"""

UPDATE_AGENT_STATE = """
mutation UpdateAgentState($agentId: ID!, $state: ScheduleTaskState!, $reason: String) {
  updateAgentState(agentId: $agentId, state: $state, reason: $reason) { __typename }
}
"""

GET_AGENT = """
query GetAgent($id: String!, $workspaceID: ID, $includeDraft: Boolean) {
  agent(id: $id, workspaceID: $workspaceID, includeDraft: $includeDraft) {
    id isDraft version scheduleId createdAt updatedAt
    specification { agentName analysisDomainId analysisDescription useDeepAnalysis }
    timing { intervalInMins startTime cronExpression cronTimezone }
  }
}
"""

LIST_AGENTS = """
query ListAgents($workspaceID: ID) {
  agents(workspaceID: $workspaceID) { id isDraft scheduleId specification { agentName analysisDomainId } }
}
"""

DELETE_DOMAIN = """
mutation DeleteDomain($id: ID!) { deleteDomain(id: $id) { __typename } }
"""


# Live App build: the prompt is an ordinary user message in a conversation created
# with liveAppEditPolicy EDIT, carrying the app's dashboard as the active reference.
SEND_USER_MESSAGE_LIVE_APP = """
mutation SendUserMessageLiveApp($conversationId: String!, $domainId: String, $query: DeltaInput!, $workspaceId: String,
                                $activeDashboardReference: DashboardReferenceInput, $dashUxRenderTarget: DashUxRenderTarget, $chatMode: ChatMode) {
  sendUserMessage(conversationId: $conversationId, domainId: $domainId, query: $query, workspaceId: $workspaceId,
                  activeDashboardReference: $activeDashboardReference, dashUxRenderTarget: $dashUxRenderTarget, chatMode: $chatMode) {
    code
    message
  }
}
"""

CHAT_MESSAGES = """
query ChatMessages($conversationId: String!) {
  chatMessages(conversationId: $conversationId) {
    nodes { id sender createdAt body { ops { insert { text externalMarkdownText } } } }
  }
}
"""


# Current product path for adding a database's tables to a domain: browse the
# connection's hierarchy for table ids, then add them to the relationship graph.
# (addDatabaseToDomain still exists but 500s with "reading 'tables'" on new
# connections, verified 2026-10-12.)
DATABASE_HIERARCHY_WITH_TABLES = """
query DatabaseHierarchyWithTables($connectionId: String!, $databaseName: String!) {
  databaseHierarchyWithTables(connectionId: $connectionId, databaseName: $databaseName) {
    nodes { name tables { id name displayName type numColumns } }
  }
}
"""

UPDATE_DOMAIN_RELATIONSHIP_GRAPH_DELTAS = """
mutation UpdateDomainRelationshipGraphDeltas($input: RelationshipGraphDeltaInput!) {
  updateDomainRelationshipGraphDeltas(input: $input) {
    id version
    databases { name tables { id name } }
  }
}
"""


# Domain Health tab: fire-and-forget analysis run (the pipeline never acts on its suggestions).
TRIGGER_DOMAIN_HEALTH_CHECK = """
mutation TriggerDomainHealthCheck($domainId: String!) {
  triggerDomainHealthCheck(domainId: $domainId) { status { code message } jobRunId alreadyQueued }
}
"""


DELETE_AGENT = """
mutation DeleteAgent($id: String!) { deleteAgent(id: $id) }
"""

DELETE_APP = """
mutation DeleteApp($appId: ID!) { deleteApp(appId: $appId) { code message } }
"""

CONNECTION_UPDATE = """
mutation ConnectionUpdate($id: ID!, $details: ConnectionDetailsInput!, $skipValidation: Boolean) {
  connectionUpdate(id: $id, details: $details, skipValidation: $skipValidation) {
    id details { name snowflake { databaseFilters } teradata { databaseFilters } }
  }
}
"""


# ---------------------------------------------------------------- S3 datasets (unstructured files in the customer's bucket)
# connectionCreate(details: ConnectionDetailsInput{connectionType: S3, dataSourceType: FILE, s3: S3ConnectionConfigInput})
# -> createConnectionDataset(connectionId, dataset: DatasetInput{name, s3DatasetConfigurationV2{connectionId, prefix}})
# -> triggerDatasetCrawl(datasetId, domainId) -> setDomainDatasetReference(input: DomainDatasetReferenceInput)
# -> read back domainDatasetReferences(domainId). Verified on proddemo 2026-10-16 by introspection.
CREATE_CONNECTION_DATASET = """
mutation CreateConnectionDataset($connectionId: ID!, $dataset: DatasetInput!) {
  createConnectionDataset(connectionId: $connectionId, dataset: $dataset) { id name ownerConnectionId crawlJobStatus extractionTableName }
}
"""

CONNECTION_DATASETS = """
query ConnectionDatasets($connectionId: ID!) {
  connectionDatasets(connectionId: $connectionId) { id name ownerConnectionId crawlJobStatus extractionTableName }
}
"""

TRIGGER_DATASET_CRAWL = """
mutation TriggerDatasetCrawl($datasetId: String!, $domainId: String!) {
  triggerDatasetCrawl(datasetId: $datasetId, domainId: $domainId) { status { code message } }
}
"""

SET_DOMAIN_DATASET_REFERENCE = """
mutation SetDomainDatasetReference($input: DomainDatasetReferenceInput!) {
  setDomainDatasetReference(input: $input) { domainId datasetId revision active indexingPending indexingError }
}
"""

DOMAIN_DATASET_REFERENCES = """
query DomainDatasetReferences($domainId: ID!) {
  domainDatasetReferences(domainId: $domainId) { pendingFiles failedFiles references { domainId datasetId revision active indexingPending indexingError facetTableName } }
}
"""

CONNECTION_DATASET_STATE = """
query ConnectionDataset($datasetId: ID!) {
  connectionDataset(datasetId: $datasetId) { totalFiles matchingFiles extractedFiles dataset { id name crawlJobStatus } }
}
"""


# ---------------------------------------------------------------------------
# Domain skills (verified against the live proddemo schema 2026-10-27).
# A skill is a markdown document with `name:` / `description:` frontmatter; the agent sees
# name + description, picks one, then loads the body. `createDomainSkill(input:
# CreateDomainSkillInput{domainId, skillMarkdown, availability: [CHAT|COPILOT|AGENTS], draftId})`
# returns `Skill`; updates need the current `version`. The context extractor's SKILL agent
# proposes skills as `UPSERT_SKILL` modeling suggestions.
DOMAIN_SKILLS = """
query DomainSkills($domainId: ID!, $includeMarkdown: Boolean) {
  domainSkills(domainId: $domainId, includeMarkdown: $includeMarkdown) {
    id version name description isActive isSystemGenerated availability skillMarkdown danglingSchemaRefs updatedAt
  }
}
"""

CREATE_DOMAIN_SKILL = """
mutation CreateDomainSkill($input: CreateDomainSkillInput!) {
  createDomainSkill(input: $input) {
    id version name description isActive availability
  }
}
"""

UPDATE_DOMAIN_SKILL = """
mutation UpdateDomainSkill($input: UpdateDomainSkillInput!) {
  updateDomainSkill(input: $input) {
    id version name description isActive availability
  }
}
"""

SET_DOMAIN_SKILL_ACTIVE = """
mutation SetDomainSkillActive($id: ID!, $domainId: ID!, $isActive: Boolean!) {
  setDomainSkillActive(id: $id, domainId: $domainId, isActive: $isActive) {
    id version name isActive
  }
}
"""
