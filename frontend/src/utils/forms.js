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
  if (role === 'company') return 'Nhà tuyển dụng';
  if (role === 'admin') return 'Quản trị viên';
  return 'Ứng viên';
}
