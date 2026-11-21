export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'CONSULTANT' | 'CLIENT';
  client_slug?: string | null;
  is_blocked: boolean;
  created_at: string;
  last_login?: string;
  salt?: string;
  password_hash?: string;
}

export const INITIAL_USERS: UserProfile[] = [
  {
    id: "usr_admin_02",
    email: "admin@nttdata.com",
    full_name: "Socio Administrador NTT DATA",
    role: "ADMIN",
    client_slug: null,
    is_blocked: false,
    created_at: "2026-01-01T00:00:00Z",
    salt: "3acc5628a84217590aedb64aefa6941c",
    password_hash: "5ab2b4c92e9bb6fc3215e4d801cb28d604c15f12906a3709379b7c28e6e53b4595de59653e513021b947de2cf68960275231369f30ce19f0fb445eb5fc08f56c",
    last_login: "2026-11-16T16:29:28.459Z"
  },
  {
    id: "usr_client_01",
    email: "ciso@nordicgrid.de",
    full_name: "CISO · Nordic Grid Power GmbH",
    role: "CLIENT",
    client_slug: "nordic_grid_power_gmbh",
    is_blocked: false,
    created_at: "2026-01-01T00:00:00Z",
    salt: "f32463526eb0c4ef56c4979c404c0097",
    password_hash: "ac52859ec230f185df4343e41174d6828652204834b092618e8d1ee393b1268124b9a1a7956f5a89899fa4a13440045be1b420dd7c54db29e136bd7e7ccc161c"
  },
  {
    id: "usr_client_02",
    email: "cio@nordicgrid.de",
    full_name: "CIO Nordic Grid Power",
    role: "CLIENT",
    client_slug: "nordic_grid_power_gmbh",
    is_blocked: false,
    created_at: "2026-01-01T00:00:00Z",
    salt: "11d3682d8778a8cc2e25e32565f67721",
    password_hash: "709b8994e1ef60e6f6b4c905f7a8c7ae8c3a17af143609775d71ba3b291a76c7f8e86a2b3ba8843fd225db3583534bf0398fbcd4d26df90d8c57e246f24a4f97"
  },
  {
    id: "usr_client_03",
    email: "seguridad@repsol.com",
    full_name: "Responsable Ciberseguridad · Repsol Global",
    role: "CLIENT",
    client_slug: "repsol_energia_global",
    is_blocked: false,
    created_at: "2026-01-01T00:00:00Z",
    salt: "8e4d53e45000eea41a1dadc0f2e54daa",
    password_hash: "4c3c05b1ebd1b2c45c3138061ac35eea5c5e614956bd347244207158876de7d1b11d16dba40532cc148575d5737cd396ac832e7e848ba1354913b60d2165bdd5"
  },
  {
    id: "usr_client_04",
    email: "auditor@bancosantander.es",
    full_name: "Auditor de Riesgo · Banco Santander",
    role: "CLIENT",
    client_slug: "banco_santander_corporacion",
    is_blocked: false,
    created_at: "2026-01-01T00:00:00Z",
    salt: "d0a5ca2499371fa77d0432ae649bf92c",
    password_hash: "ecf76c29a0f9eaf35a9595b00089820e05662c21ff2122ece5c49cd6a8f9eb77b33177b4a873cc6834122e207e4ec48bd9db15a671bd7e1dac47654a2314e47c"
  },
  {
    id: "usr_client_05",
    email: "cliente@molins.com",
    full_name: "Responsable IT Molins",
    role: "CLIENT",
    client_slug: "molins",
    is_blocked: false,
    created_at: "2026-01-01T00:00:00Z",
    salt: "6c2348cdb760223345fe534653e1a435",
    password_hash: "4ab7c9ea968ade9e3de1dadb222cd0f06f77af940afb521d8e4b934e64d83eedde2b52d394456311c1a964d24b0ddd7e559d773d36fd6d27a1c881cd083a49d5"
  },
  {
    id: "usr_1794836406248_t0uwv",
    "email": "jsanchhi@nttdata.com",
    "full_name": "José Javier Sánchez Hidalgo",
    "role": "ADMIN",
    "client_slug": null,
    "is_blocked": false,
    "salt": "1133f3ee4c55d301baaf95c6e0069ec9",
    "password_hash": "bdd01fe0952c250004f45104c7ed21a813489fd9e6aeb7c519e480a35b4dfb399277af3cd8d08751c713e9181e48c68dbdfb01b00e0d0c723a0aa97e81eb3aa7",
    "created_at": "2026-11-16T13:40:06.248Z",
    "last_login": "2026-11-16T16:38:15.227Z"
  },
  {
    id: "usr_1794846629130_1q4uq",
    "email": "jsanchhi@emeal.nttdata.com",
    "full_name": "Consultor",
    "role": "CONSULTANT",
    "client_slug": null,
    "is_blocked": false,
    "salt": "c4b1294b4d31734268d2439e2708c7d4",
    "password_hash": "82a067e0f816cc2401dc8d5605ee1ca4b616fb9b677f02540414c70c336b83b436731700c4133efce7700f38e372b3334b5cea34d17f7b6d2a57feee20be2d4b",
    "created_at": "2026-11-16T16:30:29.130Z",
    "last_login": "2026-11-16T16:31:01.808Z"
  },
  {
    id: "usr_admin_01",
    email: "director@nttdata.com",
    full_name: "Director de Práctica Cloud & Soberanía",
    role: "ADMIN",
    client_slug: null,
    is_blocked: false,
    salt: "15892841ae28664a18fee8836f0f538c",
    password_hash: "ac4d5fc34929d4092ae90ba81e10f6ae332e2fc54db1aa7a271918076f8ebe8e441b8350e265e20389f3106131bcb8d9e0702fdb22456aafe6bd7e046ed53205",
    created_at: "2026-11-16T16:35:01.926Z",
    last_login: "2026-11-18T12:57:39.370Z"
  },
  {
    id: "usr_consultant_01",
    email: "consultor@nttdata.com",
    full_name: "Consultor Senior NTT DATA",
    role: "CONSULTANT",
    client_slug: null,
    is_blocked: false,
    created_at: "2026-11-16T16:36:32.152Z",
    salt: "7331335af16225a6fb0aed7d016ebaf4",
    password_hash: "7b28ba19ef440db4a8d51c4f69a5d8ebef8106ca5c0a66bf82572deea04f81380a791d15199fe534fda67a75ceac9d4eea6709dd6b8bb4cb0ca60f83ac06d5a0",
    last_login: "2026-11-16T16:36:44.031Z"
  }
];
