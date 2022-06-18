-- auto-generated definition
create table EatenFood
(
    Id             int identity
        constraint EatenFood_pk
            primary key,
    TelegramUserId nvarchar(50) not null,
    FoodId         int          not null
        constraint FK_EatenFood_Food_Id
            references Food,
    WeightGrams    decimal(18, 2),
    AddedOn        datetime2    not null
)
go

create index TelegramUserId_index
    on EatenFood (TelegramUserId)
go

create index AddedOn_index
    on EatenFood (AddedOn desc)
go

-- auto-generated definition
create table Food
(
    Id                  int identity
        constraint Food_pk
            primary key,
    TelegramUserId      nvarchar(50)  not null,
    Name                nvarchar(200) not null,
    CaloriesPer100Grams decimal(18, 2),
    AddedOn             datetime2     not null,
    CaloriesPerPortion  decimal(18, 2),
    constraint chkCaloriesIsSet
        check ([Food].[CaloriesPer100Grams] IS NOT NULL OR [Food].[CaloriesPerPortion] IS NOT NULL)
)
go

create index Name_index
    on Food (Name)
go

create index TelegramUserId_index
    on Food (TelegramUserId)
go

create index AddedOn_index
    on Food (AddedOn desc)
go

-- auto-generated definition
create table Weight
(
    Id              int identity
        constraint Weight_pk
            primary key,
    TelegramUserId  nvarchar(50)   not null,
    WeightKilograms decimal(18, 2) not null,
    AddedOn         datetime2      not null
)
go

create index TelegramUserId_index
    on Weight (TelegramUserId)
go

create index AddedOn_index
    on Weight (AddedOn desc)
go


