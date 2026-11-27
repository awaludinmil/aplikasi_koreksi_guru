class UserModel {
  final int userId;
  final String username;
  final String namaLengkap;

  UserModel({
    required this.userId,
    required this.username,
    required this.namaLengkap,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      userId: json['user_id'] as int,
      username: json['username'] as String,
      namaLengkap: json['full_name'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
        'user_id': userId,
        'username': username,
        'full_name': namaLengkap,
      };
}
