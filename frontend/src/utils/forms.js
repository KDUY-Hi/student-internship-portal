export function profileFormFromApi(profile) {
  return {
    university: profile?.university || '',
    major: profile?.major || '',
    skills: profile?.skills || '',
    gpa: profile?.gpa ?? '',
    experience: profile?.experience || '',
    github: profile?.github || '',
    linkedin: profile?.linkedin || '',
    cv_url: profile?.cv_url || '',
  };
}

export function companyFormFromApi(profile) {
  return {
    company_name: profile?.company_name || '',
    description: profile?.description || '',
    website: profile?.website || '',
    address: profile?.address || '',
    logo_url: profile?.logo_url || '',
  };
}

export function roleLabel(role) {
  if (role === 'company') return 'Doanh nghiệp';
  if (role === 'admin') return 'Quản trị viên';
  return 'Sinh viên';
}

export function forumPostTypeLabel(type) {
  const labelMap = {
    Question: 'Câu hỏi',
    'Academic Post': 'Bài học thuật',
    'Experience Sharing': 'Chia sẻ kinh nghiệm',
    Resource: 'Tài liệu',
    Discussion: 'Thảo luận',
  };
  return labelMap[type] || type;
}
