SET XACT_ABORT ON;

IF OBJECT_Id('dbo.Brands', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.Brands (
    Id         INT IdENTITY(1,1) PRIMARY KEY,
    Name        VARCHAR(150) NOT NULL,
    Href        VARCHAR(255) NOT NULL,
    CreatedAt  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    LastUpdated  DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
  );
END;

IF OBJECT_Id('dbo.Models', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.Models(
    [Id]          INT IdENTITY(1,1) PRIMARY KEY,
    [Year]        INT            NOT NULL,
    [ModelName]  VARCHAR(150)  NOT NULL,
    [Url]         VARCHAR(255)  NOT NULL,
    [RatingUrl]  VARCHAR(255)  NULL,
    [CreatedAt]  DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME(),
    [ScrapeStatus] VARCHAR(20)   NOT NULL DEFAULT 'pending',
    [LastUpdated] DATETIME2      NULL,
    CONSTRAINT UQ_Models_ModelUrl   UNIQUE ([url]),
    CONSTRAINT UQ_Models_Year_Model UNIQUE ([Year], [ModelName])
  );
END;

IF OBJECT_Id('dbo.Details', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.Details
  (
      [Id]           INT IdENTITY(1,1) PRIMARY KEY,
      [ModelId]     INT           NOT NULL,
      [Brand]        VARCHAR(150) NULL,
      [SectionId]   VARCHAR(20)  NOT NULL,
      [SectionDesc] VARCHAR(150) NULL,
      [Label]        NVARCHAR(150) NULL,
      [Text]         NVARCHAR(500) NULL,
      [CreatedAt]   DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
      CONSTRAINT UQ_ModelDetails UNIQUE ([ModelId], [Label], [Text]),
      CONSTRAINT FK_Details_Model
        FOREIGN KEY ([ModelId]) REFERENCES dbo.Models ([Id])
        ON DELETE CASCADE
  );

  CREATE INDEX IX_ModelDetails_ModelId ON dbo.Details ([ModelId]);
END;

IF OBJECT_Id('dbo.HTML', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.HTML
  (
      [Id]          INT IdENTITY(1,1) PRIMARY KEY,
      [ModelId]    INT            NOT NULL,
      [HtmlContent] NVARCHAR(MAX)  NOT NULL,
      [CreatedAt]  DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME(),
      [RetrievedAt] DATETIME2      NULL,
      CONSTRAINT FK_html_Model
        FOREIGN KEY ([ModelId]) REFERENCES dbo.Models ([Id])
        ON DELETE CASCADE
  );
END;

IF OBJECT_Id('dbo.Failed', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.Failed
  (
      [Id]         INT IdENTITY(1,1) PRIMARY KEY,
      [ModelId]   INT           NOT NULL,
      [Url]        VARCHAR(500) NOT NULL,
      [Reason]     VARCHAR(500) NOT NULL,
      [CreatedAt] DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME(),
      CONSTRAINT FK_Failed_Model
        FOREIGN KEY ([ModelId]) REFERENCES dbo.Models ([Id])
        ON DELETE CASCADE
  );
END;
